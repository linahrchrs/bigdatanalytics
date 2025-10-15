from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import os
from werkzeug.utils import secure_filename
from detector import PlagiarismDetector
from preprocessing import extract_text, preprocess_text, validate_document, get_document_stats
import shutil

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'doc'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Global detector instance
detector = None


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def clear_uploads_folder():
    """Clear the uploads folder."""
    if os.path.exists(UPLOAD_FOLDER):
        shutil.rmtree(UPLOAD_FOLDER)
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route('/')
def index():
    """Main upload page."""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_files():
    """Handle file uploads and process them."""
    global detector
    
    # Check if files were uploaded
    if 'files' not in request.files:
        flash('No files uploaded', 'error')
        return redirect(url_for('index'))
    
    files = request.files.getlist('files')
    
    if len(files) < 2:
        flash('Please upload at least 2 documents for comparison', 'error')
        return redirect(url_for('index'))
    
    # Get detection parameters
    try:
        k = int(request.form.get('k', 5))
        num_hashes = int(request.form.get('num_hashes', 100))
        num_bands = int(request.form.get('num_bands', 20))
        threshold = float(request.form.get('threshold', 0.3))
        remove_stopwords = request.form.get('remove_stopwords') == 'on'
    except ValueError:
        flash('Invalid parameters', 'error')
        return redirect(url_for('index'))
    
    # Clear previous uploads
    clear_uploads_folder()
    
    # Initialize detector
    detector = PlagiarismDetector(
        k=k,
        num_hashes=num_hashes,
        num_bands=num_bands,
        threshold=threshold
    )
    
    processed_files = []
    errors = []
    
    # Process each file
    for file in files:
        if file and file.filename:
            if not allowed_file(file.filename):
                errors.append(f"{file.filename}: Unsupported file format")
                continue
            
            try:
                # Save file
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                # Extract and preprocess text
                text = extract_text(filepath)
                processed_text = preprocess_text(text, remove_stopwords=remove_stopwords)
                
                # Validate document
                if not validate_document(processed_text):
                    errors.append(f"{filename}: Document too short or empty")
                    continue
                
                # Add to detector
                doc_id = detector.add_document(processed_text, filename)
                
                # Get stats
                stats = get_document_stats(processed_text)
                processed_files.append({
                    'id': doc_id,
                    'filename': filename,
                    'stats': stats
                })
                
            except Exception as e:
                errors.append(f"{file.filename}: {str(e)}")
    
    if len(processed_files) < 2:
        flash('Not enough valid documents for comparison', 'error')
        if errors:
            for error in errors:
                flash(error, 'error')
        return redirect(url_for('index'))
    
    # Show any errors
    if errors:
        for error in errors:
            flash(error, 'warning')
    
    flash(f'Successfully processed {len(processed_files)} documents', 'success')
    return redirect(url_for('results'))


@app.route('/results')
def results():
    """Display plagiarism detection results."""
    global detector
    
    if detector is None:
        flash('No documents have been uploaded yet', 'error')
        return redirect(url_for('index'))
    
    # Generate report
    report = detector.generate_report()
    stats = detector.get_statistics()
    
    return render_template('results.html', report=report, stats=stats)


@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """API endpoint for programmatic analysis."""
    global detector
    
    try:
        data = request.get_json()
        
        if 'documents' not in data or len(data['documents']) < 2:
            return jsonify({'error': 'At least 2 documents required'}), 400
        
        # Initialize detector
        params = data.get('parameters', {})
        detector = PlagiarismDetector(
            k=params.get('k', 5),
            num_hashes=params.get('num_hashes', 100),
            num_bands=params.get('num_bands', 20),
            threshold=params.get('threshold', 0.3)
        )
        
        # Process documents
        for doc in data['documents']:
            text = preprocess_text(doc['text'], remove_stopwords=params.get('remove_stopwords', False))
            detector.add_document(text, doc.get('filename', 'unnamed'))
        
        # Generate report
        report = detector.generate_report()
        stats = detector.get_statistics()
        
        return jsonify({
            'report': report,
            'statistics': stats
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/clear')
def clear():
    """Clear all uploaded files and reset detector."""
    global detector
    detector = None
    clear_uploads_folder()
    flash('All documents cleared', 'success')
    return redirect(url_for('index'))


@app.errorhandler(413)
def too_large(e):
    """Handle file too large error."""
    flash('File is too large. Maximum size is 16MB', 'error')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)