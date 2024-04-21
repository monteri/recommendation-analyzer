import numpy as np
import joblib
import pandas as pd
from lightfm import LightFM
from lightfm.data import Dataset
from lightfm.evaluation import precision_at_k, recall_at_k, auc_score


def save_model(model, model_path):
    joblib.dump(model, model_path)


def save_mapping(mapping, mapping_path):
    joblib.dump(mapping, mapping_path)


def load_model(model_path='model.pkl'):
    try:
        return joblib.load(model_path)
    except FileNotFoundError:
        print(f"Model file not found at path: {model_path}")
        return None
    except Exception as e:
        print(f"An error occurred while loading the model: {e}")
        return None


def load_mapping(mapping_path):
    try:
        return joblib.load(mapping_path)
    except FileNotFoundError:
        print(f"Mapping file not found at path: {mapping_path}")
        return None
    except Exception as e:
        print(f"An error occurred while loading the mapping: {e}")
        return None


def get_recommendations(model, dataset, user_id, products, item_features, N=6):
    # Get the internal representation of all item IDs
    item_ids = np.arange(item_features.shape[0])
    # Convert the user string ID to integer ID
    user_internal_id = dataset.mapping()[0][user_id]

    # Predict the scores for all items
    scores = model.predict(user_internal_id, item_ids, item_features=item_features)
    print('scores', scores)
    # Rank items in descending order based on the scores
    top_items = item_ids[np.argsort(-scores)][:N]

    # Print out the results
    recommendations = list(filter(lambda x: x['id'] in top_items, products))
    return recommendations


def generate_event_dataset(event_data, product_data):
    """
    Prepares the dataset for use with LightFM by creating a mapping of users, items, and item features.
    """
    # Convert event and product data to DataFrames
    events_df = pd.DataFrame(event_data)
    products_df = pd.DataFrame(product_data)

    # Process event data to map 'param' to 'id' for brand and type events
    brand_to_id = products_df.drop_duplicates('brand').set_index('brand')['id'].to_dict()
    type_to_id = products_df.drop_duplicates('type').set_index('type')['id'].to_dict()

    events_df['item_id'] = events_df.apply(
        lambda x: x['param'] if x['activity'] == 'buy' else brand_to_id.get(x['param'], None) if x['activity'] == 'brand' else type_to_id.get(x['param'], None),
        axis=1
    )

    # Remove events that could not be mapped to an item_id
    events_df.dropna(subset=['item_id'], inplace=True)

    # Make sure to convert item IDs to strings if they are not already
    events_df['item_id'] = events_df['item_id'].astype(str)
    products_df['id'] = products_df['id'].astype(str)

    # Initialize dataset object
    dataset = Dataset()

    # Fit dataset to include all users, items, and item features
    dataset.fit(
        users=events_df['user_id'].unique(),
        items=pd.concat([events_df['item_id'], products_df['id']]).unique(),
        item_features=products_df['type'].unique().tolist() + products_df['brand'].unique().tolist()
    )

    # When creating item tuples, use the string type of the IDs
    item_tuples = products_df.apply(lambda row: (str(row['id']), [row['type'], row['brand']]), axis=1).tolist()

    # Build interaction matrix
    (interactions, weights) = dataset.build_interactions(zip(events_df['user_id'], events_df['item_id']))

    # Create item features
    item_features = dataset.build_item_features(item_tuples, normalize=False)

    return dataset, interactions, item_features


def train_model(interactions, item_features, epochs=20):
    """
    Trains the LightFM model.
    """
    model = LightFM(no_components=30, loss='warp')
    model.fit(interactions, item_features=item_features, epochs=epochs)
    return model


def evaluate_model(model, test_interactions, item_features):
    """
    Evaluates the trained model.
    """
    precision = precision_at_k(model, test_interactions, item_features=item_features, k=5).mean()
    recall = recall_at_k(model, test_interactions, item_features=item_features, k=5).mean()
    auc = auc_score(model, test_interactions, item_features=item_features).mean()

    return precision, recall, auc
