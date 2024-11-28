from flask import Flask, request, jsonify, render_template
import os
from dotenv import load_dotenv
import openai
import google.generativeai as genai
import numpy as np
from sklearn.decomposition import PCA
import http.client
import json

app = Flask(__name__)
load_dotenv()

# Configure API keys
openai.api_key = os.getenv('OPENAI_API_KEY')
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
CLOUDFLARE_API_KEY = os.getenv('CLOUDFLARE_API_KEY')
CLOUDFLARE_ACCOUNT_ID = os.getenv('CLOUDFLARE_ACCOUNT_ID')

def get_openai_embedding(texts):
    response = openai.embeddings.create(
        model="text-embedding-ada-002",
        input=texts
    )
    return [item.embedding for item in response.data]

def get_gemini_embedding(texts):
    model = genai.GenerativeModel('embedding-001')
    embeddings = []
    for text in texts:
        embedding = model.embed_content(text)
        embeddings.append(embedding.embedding)
    return embeddings

def get_cloudflare_embedding(texts):
    try:
        conn = http.client.HTTPSConnection("api.cloudflare.com")
        
        # If multiple texts are provided, process them one by one
        embeddings = []
        for text in texts:
            payload = json.dumps({
                "text": text
            })
            
            headers = {
                'Content-Type': "application/json",
                'Authorization': f"Bearer {CLOUDFLARE_API_KEY}"
            }
            
            endpoint = f"/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/@cf/baai/bge-large-en-v1.5"
            conn.request("POST", endpoint, payload, headers)
            
            response = conn.getresponse()
            data = json.loads(response.read().decode("utf-8"))
            print(data)
            
            if not data.get('success', False):
                error_msg = data.get('errors', [{'message': 'Unknown error'}])[0].get('message', 'Unknown error')
                raise Exception(f"API Error: {error_msg}")
            
            # Extract the embedding from the new response format
            result = data.get('result', {})
            embedding_data = result.get('data', [[]])[0]  # Get the first (and only) embedding array
            
            if not embedding_data:
                raise Exception(f"No valid embedding returned for text: {text}")
            
            embeddings.append(embedding_data)
        
        return embeddings
        
    except Exception as e:
        print(f"Error in get_cloudflare_embedding: {str(e)}")
        raise Exception(f"Cloudflare API Error: {str(e)}")

def reduce_dimensions(embeddings):
    # Convert embeddings to numpy array
    embeddings_array = np.array(embeddings)
    
    # Ensure we have a 2D array
    if len(embeddings_array.shape) != 2:
        raise Exception("Invalid embedding format")
    
    pca = PCA(n_components=3)
    reduced = pca.fit_transform(embeddings_array)
    return reduced.tolist()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get_embedding', methods=['POST'])
def get_embedding():
    data = request.json
    texts = [text.strip() for text in data['text'].split(',')]
    model = data['model']
    
    try:
        if model == 'openai':
            embeddings = get_openai_embedding(texts)
        elif model == 'gemini':
            embeddings = get_gemini_embedding(texts)
        elif model == 'cloudflare':
            embeddings = get_cloudflare_embedding(texts)
        else:
            return jsonify({'error': 'Invalid model selection'}), 400
        
        # Print embeddings shape for debugging
        print(f"Embeddings shape: {np.array(embeddings).shape}")
        
        reduced_embeddings = reduce_dimensions(embeddings)
        return jsonify({
            'embeddings': embeddings,
            'reduced_embeddings': reduced_embeddings,
            'labels': texts
        })
    except Exception as e:
        print(f"Error in get_embedding: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
