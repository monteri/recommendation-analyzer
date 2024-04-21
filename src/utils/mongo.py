from datetime import datetime

from pymongo import MongoClient

client = MongoClient('mongodb://root:root@localhost:27017/')  # Update with your credentials and host
db = client['events_db']  # Use the database 'events_db'
collection = db['events']  # Use the collection 'events'


def insert_event(event_data):
    """Insert event data into the MongoDB collection."""
    try:
        event_data['timestamp'] = datetime.utcnow()
        collection.insert_one(event_data)
    except Exception as e:
        print(f"An error occurred: {e}")


def get_event_data(batch_size=10000):
    """Retrieve the last 10,000 event data records from MongoDB."""
    events = collection.find({}).sort('timestamp', -1).limit(batch_size)
    return list(events)
