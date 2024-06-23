import pandas as pd
from transformers import AutoTokenizer, TFAutoModel
import tensorflow as tf
import faiss
import pathlib, os

# Set environment variable to handle OpenMP error
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Define the pretrained model
model_ckpt = "sentence-transformers/multi-qa-mpnet-base-dot-v1"
dataset_filepath = "./extracted_data.csv"


# Define a function to perform CLS pooling on the model output https://huggingface.co/learn/nlp-course/chapter5/6?fw=tf#creating-text-embeddings
def cls_pooling(model_output):
    # Extracts the embeddings for the [CLS] token from the model output
    return model_output.last_hidden_state[:, 0]


# Define a function to get embeddings for a list of user requests
def get_embeddings(User_Request_list):
    encoded_input = tokenizer(
        User_Request_list, padding=True, truncation=True, return_tensors="tf"
    )
    # Encodes a list of user requests and generates their embeddings using the transformer model.
    model_output = model(encoded_input)
    # Extract the [CLS] token embeddings from the model outputs using cls_pooling function.
    return cls_pooling(model_output)


# Prompt user to enter a query
question = input("Enter your query: ")

# Check if the dataset file exists
if not pathlib.Path.exists(pathlib.Path(dataset_filepath)):
    raise FileNotFoundError(f"Dataset file not found in {dataset_filepath}")

# Load the dataset from csv using pandas
df = pd.read_csv(dataset_filepath)

# Check if 'User_Request' column exists in the dataset
if 'User_Request' not in df.columns:
    raise ValueError("Dataset does not contain a 'User_Request' column")

# Load tokenizer and model from the specified checkpoint
tokenizer = AutoTokenizer.from_pretrained(model_ckpt)
model = TFAutoModel.from_pretrained(model_ckpt, from_pt=True)

# Generate embeddings for all user requests in the dataset
embeddings = get_embeddings(df["User_Request"].tolist()).numpy()

# Add the generated embeddings to the DataFrame
df["embeddings"] = embeddings.tolist()

# Initialize a FAISS index and add the embeddings to it
embedding_dim = embeddings.shape[1]
index = faiss.IndexFlatL2(embedding_dim)
index.add(embeddings)

# Generate embedding for the user's question
question_embedding = get_embeddings([question]).numpy()

# Perform a search to find the nearest neighbors to the question embedding
D, I = index.search(question_embedding, k=5)

# Retrieve the results from the DataFrame based on the indices returned by the search
results = df.iloc[I[0]]

# Add the search scores to the results DataFrame
results["scores"] = D[0]

# Sort the results by scores in descending order
results = results.sort_values("scores", ascending=False)

# Display the top results to the user
for _, row in results.iterrows():
    print(f"User_Request: {row['User_Request']}")
    print(f"Score: {row['scores']}")
    print("=" * 50)
    print()
