
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ConversationHandler, ContextTypes, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from web3 import Web3
from transformers import AutoTokenizer, TFAutoModel
import tensorflow as tf
import faiss
import compile_smartcontract, nlp
import os, pathlib
import pandas as pd

# nlp vars
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
model_ckpt = "sentence-transformers/multi-qa-mpnet-base-dot-v1"
dataset_filepath = "./data/input/extracted_data.csv"

# bot relates vars
TOKEN = os.getenv("TOKEN")
# Define states for conversation
CHOOSING, TYPING_REPLY, TYPING_PRICE = range(3)

# Blockchain env vars
address = Web3.to_checksum_address(os.getenv("METAMASK_WALLET_ADDRESS"))
private_key = os.getenv("METAMASK_WALLET_PRIVATE_KEY")
w3_provider = Web3(Web3.HTTPProvider("https://rpc2.sepolia.org"))
chain_id = 11155111

# Solidity vars
sol_smartcontract_filepath = "../solidity/contracts/intent.sol"

# Load the dataset from csv using pandas
df = pd.read_csv(dataset_filepath)

# Check if 'User_Request' column exists in the dataset

# Load tokenizer and model from the specified checkpoint
tokenizer = AutoTokenizer.from_pretrained(model_ckpt)
model = TFAutoModel.from_pretrained(model_ckpt, from_pt=True)

# Generate embeddings for all user requests in the dataset
embeddings = nlp.get_embeddings(tokenizer, df["User_Request"].tolist(), model).numpy()

# Add the generated embeddings to the DataFrame
df["embeddings"] = embeddings.tolist()

# Initialize a FAISS index and add the embeddings to it
embedding_dim = embeddings.shape[1]
index = faiss.IndexFlatL2(embedding_dim)
index.add(embeddings)

if 'User_Request' not in df.columns:
    raise ValueError("Dataset does not contain a 'User_Request' column")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [
            InlineKeyboardButton("Create an intent with Etherum", callback_data='provide_input'),
            InlineKeyboardButton("Cancel", callback_data='cancel'),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('This is DiFi Matrix bot. It will help you to create an Etherum intent and fulfill it. Please follow simple steps', reply_markup=reply_markup)
    return CHOOSING


async def received_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_input = update.message.text
    try:
        # Assume we expect a number as input
        price = int(user_input)
        # Store the user input in context.user_data
        context.user_data['input_price'] = price
        await update.message.reply_text(f'Thanks! You proposed a price of {price}.\n Please wait for smartcontract deployment')

        tx_hash = compile_smartcontract.deploy_smartcontract(w3_provider, chain_id, private_key, address, sol_smartcontract_filepath)

        eth_scan_link = compile_smartcontract.get_eth_sepolia_scanner_link(tx_hash.hex())

        await update.message.reply_text(f'Intent smartcontract deployed with tx hash {tx_hash.hex()}.\n View in {eth_scan_link}')

    except ValueError:
        await update.message.reply_text('Invalid input. Please enter a valid number.')
        return TYPING_PRICE
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('Cancelled')
    return ConversationHandler.END


# Define the callback query handler
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == 'provide_input':
        await query.edit_message_text(text="Describe your intent")
        return TYPING_REPLY
    elif query.data == 'cancel':
        await query.edit_message_text(text="See you next time")
        return ConversationHandler.END


async def received_intent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_input = update.message.text
    context.user_data['input_intent'] = user_input
    await update.message.reply_text("Thanks for your intent! Now, propose your price.")
    return TYPING_PRICE


async def semantic_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_input = update.message.text

    # Generate embedding for the user's question
    question_embedding = nlp.get_embeddings([user_input]).numpy()

    # Perform a search to find the nearest neighbors to the question embedding
    D, I = index.search(question_embedding, k=5)

    # Retrieve the results from the DataFrame based on the indices returned by the search
    results = df.iloc[I[0]]

    # Add the search scores to the results DataFrame
    results["scores"] = D[0]

    # Sort the results by scores in descending order
    results = results.sort_values("scores", ascending=False)

    for _, row in results.iterrows():
        match = row['User_Request']
        score = row['scores']
        message = f"{match} -- Confidence score: {score}"
        print(message)
        await context.bot.send_message(chat_id=update.message.chat_id, text=message)


def main() -> None:
    if not pathlib.Path.exists(pathlib.Path(sol_smartcontract_filepath)):
        raise FileNotFoundError(f"Smartcontract file path not found: {sol_smartcontract_filepath}")

    if not pathlib.Path.exists(pathlib.Path(dataset_filepath)):
        raise FileNotFoundError(f"Dataset file not found in {dataset_filepath}")

    application = ApplicationBuilder().token(TOKEN).build()

    print("bot launched")

    # Define the conversation handler with the states CHOOSING and TYPING_REPLY
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [
                CallbackQueryHandler(button),
            ],
            TYPING_REPLY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, received_intent),
            ],
            TYPING_PRICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, received_price),
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)

    # application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, nlp.semantic_search))

    application.run_polling()



# Check if the dataset file exists
# if not pathlib.Path.exists(pathlib.Path(dataset_filepath)):
#     raise FileNotFoundError(f"Dataset file not found in {dataset_filepath}")
#
# # Load the dataset from csv using pandas
# df = pd.read_csv(dataset_filepath)
#
# # Check if 'User_Request' column exists in the dataset
# if 'User_Request' not in df.columns:
#     raise ValueError("Dataset does not contain a 'User_Request' column")
#
# # Load tokenizer and model from the specified checkpoint
# tokenizer = AutoTokenizer.from_pretrained(model_ckpt)
# model = TFAutoModel.from_pretrained(model_ckpt, from_pt=True)
#
# # Generate embeddings for all user requests in the dataset
# embeddings = get_embeddings(df["User_Request"].tolist()).numpy()
#
# # Add the generated embeddings to the DataFrame
# df["embeddings"] = embeddings.tolist()
#
# # Initialize a FAISS index and add the embeddings to it
# embedding_dim = embeddings.shape[1]
# index = faiss.IndexFlatL2(embedding_dim)
# index.add(embeddings)


if __name__ == '__main__':
    main()
