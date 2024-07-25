from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_required, current_user
from .models import User, Note
from . import db
import json
from werkzeug.utils import secure_filename
import os
import speech_recognition as sr
from pydub import AudioSegment

views = Blueprint('views', __name__)


@views.route('/test_pico')
def test_pico():
    return render_template("test_pico.html")

@views.route('/')
def home():
    return render_template("home.html", user=current_user, notes=notes)

@views.route('/notes', methods=['GET', 'POST'])
@login_required
def notes():
    notes = Note.query.filter_by(user_id=current_user.id).order_by(Note.date.desc()).all() 
    # print([note.date for note in notes])
    # if request.method == 'POST': 
    #     note = request.form.get('note')#Gets the note from the HTML 

    #     if len(note) < 1:
    #         flash('Note is too short!', category='error') 
    #     else:
    #         new_note = Note(content=note, user_id=current_user.id)  #providing the schema for the note 
    #         db.session.add(new_note) #adding the note to the database 
    #         db.session.commit()
    #         flash('Note added!', category='success')

    return render_template("notes.html", user=current_user, notes=notes)

@views.route('/add_note', methods=['POST'])
def add_note():
    data = request.json
    title = data.get('title')
    content = data.get('content')
    
    new_note = Note(title=title, content=content, user_id=current_user.id)
    db.session.add(new_note)
    db.session.commit()
    
    return jsonify({"message": "Note added successfully", "id": new_note.id}), 200 #render_template("home.html", user=current_user)#   

@views.route('/save-note', methods=['POST'])
def save_note():
    data = request.json
    note_id = data.get('id')
    title = data.get('title')
    content = data.get('content')

    try:
        note = Note.query.get(note_id)
        if note:
            note.title = title
            note.content = content
            db.session.commit()
            return jsonify({'success': True, 'message': 'Note updated successfully'}), 200
        else:
            return jsonify({'success': False, 'message': 'Note not found'}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@views.route('/delete-note', methods=['POST'])
def delete_note():  
    note = json.loads(request.data) # this function expects a JSON from the INDEX.js file 
    noteId = note['noteId']
    note = Note.query.get(noteId)
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()

    return jsonify({})


@views.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})

    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(views.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        print("File saved.")
        text = transcribe_audio(filepath)
        print(text)
        print("File transcribed.")
        return jsonify({'text': text})

def transcribe_audio(filepath):
    recognizer = sr.Recognizer()
    audio = AudioSegment.from_file(filepath)
    audio.export(filepath, format="wav")
    
    with sr.AudioFile(filepath) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data)
            return text
        except sr.UnknownValueError:
            return "Could not understand audio"
        except sr.RequestError:
            return "Could not request results; check your network connection"    
