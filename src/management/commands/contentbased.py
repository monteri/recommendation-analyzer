from django.core.management.base import BaseCommand
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd

from src.data import data
from src.utils.mongo import get_event_data
from src.utils.ml_utils import save_model


class Command(BaseCommand):
    help = 'Train the content-based recommendation model based on event and product data from MongoDB'

    def handle(self, *args, **options):
        # Retrieve event and product data
        event_data = get_event_data()
        product_data = data  # Assuming 'data' contains your products information

        # Convert product data to DataFrame and create a features column
        products_df = pd.DataFrame(product_data)
        products_df['features'] = products_df['brand'] + " " + products_df['type']

        # Create a TF-IDF Vectorizer and fit it to the products' features
        tfidf_vectorizer = TfidfVectorizer()
        item_features = tfidf_vectorizer.fit_transform(products_df['features'])

        # Save the TF-IDF matrix and the vectorizer for later use in generating recommendations
        save_model(tfidf_vectorizer, 'tfidf_vectorizer.pkl')
        save_model(item_features, 'item_features_matrix.pkl')

        self.stdout.write(self.style.SUCCESS('Successfully created the content-based recommendation model'))
