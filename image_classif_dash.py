import streamlit as st
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import torchvision.transforms as transforms

from torchvision.models import resnet50, ResNet50_Weights
from captum.attr import IntegratedGradients
from captum.attr import visualization as viz

# Load model with caching
@st.cache_resource
def load_model():
    model = resnet50(weights=ResNet50_Weights.IMAGENET1K_V2)
    model.eval()
    return model

# Preprocessing function
preprocess_func = ResNet50_Weights.IMAGENET1K_V2.transforms()
categories = np.array(ResNet50_Weights.IMAGENET1K_V2.meta["categories"])

def make_prediction(model, processed_img):
    probs = model(processed_img.unsqueeze(0))
    probs = probs.softmax(1)
    probs = probs[0].detach().numpy()

    prob, idxs = probs[probs.argsort()[-5:][::-1]], probs.argsort()[-5:][::-1]
    return prob, idxs

def interpret_prediction(model, processed_img, target):
    interpretation_algo = IntegratedGradients(model)
    feature_imp = interpretation_algo.attribute(processed_img.unsqueeze(0), target=int(target))
    feature_imp = feature_imp[0].numpy()
    feature_imp = feature_imp.transpose(1, 2, 0)

    return feature_imp

## Dashboard GUI
st.title("ResNet-50 Image Classifier")
upload = st.file_uploader(label="Upload Image:", type=["png", "jpg", "jpeg"])

if upload:
    try:
        # Load and process the image
        img = Image.open(upload).convert("RGB")
        st.image(img, caption='Uploaded Image', use_column_width=True)

        model = load_model()
        st.write("Model loaded successfully.")

        # Preprocess the image
        preprocess = transforms.Compose([
            transforms.Resize((224, 224)),  # Resize to match the model input
            transforms.ToTensor(),           # Convert to tensor
        ])

        preprocessed_img = preprocess(img)

        # Make predictions
        probs, idxs = make_prediction(model, preprocessed_img)
        feature_imp = interpret_prediction(model, preprocessed_img, idxs[0])

        # Visualization
        main_fig = plt.figure(figsize=(12, 3))
        ax = main_fig.add_subplot(111)
        plt.barh(y=categories[idxs][::-1], width=probs[::-1], color=["dodgerblue"] * 4 + ["tomato"])
        plt.title("Top 5 Probabilities", loc="center", fontsize=15)
        st.pyplot(main_fig, use_container_width=True)

        interp_fig, ax = viz.visualize_image_attr(feature_imp, show_colorbar=True, fig_size=(6, 6))

        col1, col2 = st.columns(2, gap="medium")

        with col1:
            main_fig = plt.figure(figsize=(6, 6))
            ax = main_fig.add_subplot(111)
            plt.imshow(img)
            plt.xticks([], [])
            plt.yticks([], [])
            st.pyplot(main_fig, use_container_width=True)

        with col2:
            st.pyplot(interp_fig, use_container_width=True)

    except Exception as e:
        st.error(f"An error occurred: {e}")
