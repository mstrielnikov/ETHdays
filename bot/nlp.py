import pandas as pd
from transformers import AutoTokenizer, TFAutoModel
import tensorflow as tf
import faiss
import os


def cls_pooling(model_output):
    # Extracts the embeddings for the [CLS] token from the model output
    return model_output.last_hidden_state[:, 0]


# Define a function to get embeddings for a list of user requests
def get_embeddings(tokenizer, User_Request_list, model):
    encoded_input = tokenizer(
        User_Request_list, padding=True, truncation=True, return_tensors="tf"
    )
    # Encodes a list of user requests and generates their embeddings using the transformer model.
    model_output = model(encoded_input)
    # Extract the [CLS] token embeddings from the model outputs using cls_pooling function.
    return cls_pooling(model_output)