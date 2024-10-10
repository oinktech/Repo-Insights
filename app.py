from flask import Flask, render_template, jsonify, send_file
from flask_cors import CORS
import requests
import matplotlib.pyplot as plt
import io
import logging
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Set up logging
logging.basicConfig(level=logging.INFO)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/<username>/repos', methods=['GET'])
def get_repos(username):
    try:
        url = f'https://api.github.com/users/{username}/repos'
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
        repos = response.json()
        
        repo_data = []
        for repo in repos:
            repo_data.append({
                'name': repo['name'],
                'stars': repo['stargazers_count'],
                'forks': repo['forks_count'],
                'created_at': datetime.strptime(repo['created_at'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d'),
                'updated_at': datetime.strptime(repo['updated_at'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d'),
                'language': repo['language'],
                'url': repo['html_url'],
            })

        return jsonify(repo_data)
    except requests.exceptions.RequestException as e:
        logging.error(f"Request error: {e}")
        return jsonify({'error': f'Unable to retrieve data for {username}'}), 500

@app.route('/api/<username>/stats-image', methods=['GET'])
def generate_stats_image(username):
    try:
        url = f'https://api.github.com/users/{username}/repos'
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
        repos = response.json()

        if not repos:
            return jsonify({'error': f'No repositories found for user {username}'}), 404

        names = [repo['name'] for repo in repos]
        stars = [repo['stargazers_count'] for repo in repos]

        # Create a horizontal bar chart
        plt.figure(figsize=(12, len(names) * 0.5))
        bars = plt.barh(names, stars, color='royalblue', edgecolor='black')

        # Add annotations for each bar
        for bar in bars:
            plt.text(bar.get_width(), bar.get_y() + bar.get_height()/2, 
                     f'{bar.get_width()}', va='center', fontsize=10, color='white')

        plt.xlabel('Stars')
        plt.title(f'Stars Count for Repositories of {username}', fontsize=14, fontweight='bold')
        plt.grid(axis='x', linestyle='--', alpha=0.7)

        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight')  # Tight layout to avoid clipping
        img.seek(0)
        plt.close()

        return send_file(img, mimetype='image/png')
    except requests.exceptions.HTTPError as e:
        logging.error(f"HTTP error: {e}")
        return jsonify({'error': f'HTTP error occurred for user {username}: {e.response.status_code}'}), 500
    except requests.exceptions.RequestException as e:
        logging.error(f"Request error: {e}")
        return jsonify({'error': f'Unable to generate image for {username}'}), 500
    except Exception as e:
        logging.error(f"General error: {e}")
        return jsonify({'error': 'An unexpected error occurred'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10000)
