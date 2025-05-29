from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from datetime import datetime
import os
from dotenv import load_dotenv
from ui.models import db, User, ChatSession, Chat
from ui.forms import LoginForm, SignupForm
from data.retriever.hybrid_retriever import rag_advisor
import markdown
load_dotenv()
# ====================
# App Initialization
# ====================

app = Flask(__name__,
            template_folder='ui/templates',
            static_folder='ui/static')
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("SQLALCHEMY_DATABASE_URI")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# ====================
# Login Manager Setup
# ====================
login_manager = LoginManager(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ====================
# Routes - Auth
# ====================
@app.route('/')
def index():
    return redirect(url_for('chat'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        user = User(username=form.username.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('chat'))
    return render_template('signup.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('chat'))
        flash('Invalid credentials.')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# ====================
# Routes - Chat
# ====================
@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    session_id = request.args.get("session")
    new_chat = request.args.get("new")

    # Start new session if needed
    if new_chat or not session_id:
        session = ChatSession(user_id=current_user.id)
        db.session.add(session)
        db.session.commit()
        return redirect(url_for("chat", session=session.id))

    session = ChatSession.query.filter_by(id=session_id, user_id=current_user.id).first_or_404()

    # Handle new message submission
    if request.method == 'POST':
        message = request.form['message']

        user_msg = Chat(session_id=session.id, message=message, timestamp=datetime.utcnow(), sender='user')
        response = rag_advisor(message)
        if response:
            response = markdown.markdown(response)
        else:
            response = "Oops!!! Sorry...."
        bot_reply = Chat(session_id=session.id, message=response, timestamp=datetime.utcnow(), sender='bot')

        db.session.add_all([user_msg, bot_reply])
        db.session.commit()

    # Get messages for this session
    messages = Chat.query.filter_by(session_id=session.id).order_by(Chat.timestamp).all()

    # Get recent chat sessions for sidebar
    recent_sessions = ChatSession.query.filter_by(user_id=current_user.id).order_by(ChatSession.id.desc()).limit(5).all()
    recent_chats = []
    for s in recent_sessions:
        first_msg = Chat.query.filter_by(session_id=s.id).order_by(Chat.timestamp).first()
        title = first_msg.message if first_msg else f"Chat {s.id}"
        recent_chats.append((s.id, title[:30]))

    return render_template('chat.html', session=session, messages=messages, recent_chats=recent_chats)


# ====================
# Routes - Chat Utilities
# ====================
@app.route('/clear_history')
@login_required
def clear_history():
    sessions = ChatSession.query.filter_by(user_id=current_user.id).all()
    for s in sessions:
        Chat.query.filter_by(session_id=s.id).delete()
        db.session.delete(s)
    db.session.commit()
    flash('Chat history cleared.')
    return redirect(url_for('chat', new=1))


@app.route('/search')
@login_required
def search():
    query = request.args.get('q', '')
    sessions = ChatSession.query.filter_by(user_id=current_user.id).all()
    matched_sessions = []
    for s in sessions:
        first_msg = Chat.query.filter_by(session_id=s.id).order_by(Chat.timestamp).first()
        if first_msg and query.lower() in first_msg.message.lower():
            matched_sessions.append((s.id, first_msg.message[:50]))  # Truncate preview
    return jsonify(matched_sessions[:5])


# ====================
# New Route - Delete Chat
# ====================
@app.route('/delete_chat', methods=['POST'])
@login_required
def delete_chat():
    data = request.get_json()
    session_id = data.get('session_id')

    if not session_id:
        return jsonify(success=False, error="No session ID provided")

    # Validate ownership
    session = ChatSession.query.filter_by(id=session_id, user_id=current_user.id).first()
    if not session:
        return jsonify(success=False, error="Chat session not found or unauthorized")

    try:
        # Delete all chats in this session
        Chat.query.filter_by(session_id=session.id).delete()
        # Delete session itself
        db.session.delete(session)
        db.session.commit()
        return jsonify(success=True)
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, error=str(e))


# ====================
# Routes - Static Pages
# ====================
@app.route('/about')
def about():
    return render_template('about.html')


# ====================
# Run App
# ====================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
