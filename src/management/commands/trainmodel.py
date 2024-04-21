from django.core.management.base import BaseCommand

from src.data import data
from src.utils.ml_utils import (
    save_model,
    generate_event_dataset,
    save_mapping,
    train_model,
    evaluate_model
)
from src.utils.mongo import get_event_data


class Command(BaseCommand):
    help = 'Train the recommendation model based on event and product data from MongoDB'

    def handle(self, *args, **options):
        # Retrieve event and product data
        event_data = get_event_data()
        product_data = data

        # Generate the event dataset
        dataset, interactions, item_features = generate_event_dataset(event_data, product_data)

        # Train the model
        model = train_model(interactions, item_features, epochs=10)

        # Evaluate the model
        precision, recall, auc = evaluate_model(model, interactions, item_features)

        # Output the evaluation results
        self.stdout.write(f"Precision at K: {precision}")
        self.stdout.write(f"Recall at K: {recall}")
        self.stdout.write(f"AUC Score: {auc}")

        # Save the model and mappings
        save_model(model, 'model.pkl')
        save_mapping(dataset, 'dataset.pkl')
        save_mapping(item_features, 'item_features.pkl')

        self.stdout.write(self.style.SUCCESS('Successfully trained the recommendation model'))