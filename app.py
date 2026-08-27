import json
import os
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
# 50MB tak ki HD Studio Photos allow karne ke liye
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
CORS(app)

DB_FILE = 'lace_catalog_db.json'

DEFAULT_DESIGNS = [
    {
        'id': 1,
        'name': 'JK11',
        'category': 'Jharkhand Lace',
        'price': 62,
        'meter': 20,
        'img': (
            'https://images.unsplash.com/photo-1528459801416-a9e53bbf4e17?w=600&q=85'
        ),
        'colors': ['Gold', 'Silver', 'Pani', 'Mett'],
    },
    {
        'id': 2,
        'name': 'Chameli-47',
        'category': 'Embroidery',
        'price': 48,
        'meter': 20,
        'img': (
            'https://images.unsplash.com/photo-1618221195710-dd6b41faaea6?w=600&q=85'
        ),
        'colors': ['Multi', 'Red', 'Navy', 'Gold'],
    },
    {
        'id': 3,
        'name': 'Crystal-KP',
        'category': 'Heavy Crystal',
        'price': 95,
        'meter': 25,
        'img': (
            'https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?w=600&q=85'
        ),
        'colors': ['Multi', 'Red', 'Navy', 'Gold'],
    },
    {
        'id': 4,
        'name': 'Jhalar-88',
        'category': 'Jhalar',
        'price': 34,
        'meter': 18,
        'img': (
            'https://images.unsplash.com/photo-1579783902614-a3fb3927b675?w=600&q=85'
        ),
        'colors': ['Multi', 'Red', 'Navy', 'Gold'],
    },
]


def load_db():
  if not os.path.exists(DB_FILE):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
      json.dump(DEFAULT_DESIGNS, f, indent=2)
    return DEFAULT_DESIGNS
  try:
    with open(DB_FILE, 'r', encoding='utf-8') as f:
      return json.load(f)
  except Exception:
    return DEFAULT_DESIGNS


def save_db(data):
  with open(DB_FILE, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)


@app.route('/api/designs', methods=['GET'])
def get_designs():
  return jsonify(load_db())


@app.route('/api/designs', methods=['POST'])
def add_design():
  req_data = request.json
  if not req_data or not req_data.get('name'):
    return jsonify({'error': 'Design Name is required'}), 400

  db = load_db()

  # Check agar design pehle se hai to update karein, warna naya insert karein
  existing_idx = next(
      (i for i, item in enumerate(db) if item['name'] == req_data.get('name')),
      None,
  )

  new_item = {
      'id': int(req_data.get('id', len(db) + 1)),
      'name': str(req_data.get('name')),
      'category': str(req_data.get('category', 'Embroidery')),
      'price': float(req_data.get('price', 45)),
      'meter': float(req_data.get('meter', 20)),
      'colors': req_data.get('colors', ['Gold', 'Silver', 'Pani', 'Mett']),
      'img': req_data.get(
          'img',
          'https://images.unsplash.com/photo-1618221195710-dd6b41faaea6?w=600&q=85',
      ),
  }

  if existing_idx is not None:
    db[existing_idx] = new_item
  else:
    db.insert(0, new_item)

  save_db(db)
  return jsonify({'message': 'Design saved successfully!', 'data': new_item}), 201


@app.route('/api/designs/<int:item_id>', methods=['DELETE'])
def delete_design(item_id):
  db = load_db()
  db = [item for item in db if item.get('id') != item_id]
  save_db(db)
  return jsonify({'message': 'Design deleted successfully'})


if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000, debug=True)