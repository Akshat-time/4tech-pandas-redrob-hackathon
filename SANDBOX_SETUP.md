# Sandbox Setup

This repo already contains a runnable demo app in `app.py` and the
dependencies in `requirements.txt`.

## What is already done

- The ranker is implemented in `India_runs_data_and_ai_challenge/ranker.py`.
- The demo app is implemented in `app.py`.
- The repository is published on GitHub.
- The submission metadata file exists at `submission_metadata.yaml`.

## What you still need to do

1. Choose a hosting platform.
   - Streamlit Cloud is the simplest choice for this repo.
   - Hugging Face Spaces also works if you prefer that.

2. Connect the GitHub repo to the platform.
   - Use `https://github.com/Akshat-time/4tech-pandas-redrob-hackathon`.
   - Point the platform at `app.py` as the main app file.

3. Deploy the app.
   - Wait for the platform to finish building the environment.
   - Confirm the app loads and displays the sample ranking table.

4. Copy the hosted app URL.
   - Paste that URL into `submission_metadata.yaml` under `sandbox_link`.

## If you use Streamlit Cloud

- Sign in to Streamlit Cloud with your GitHub account.
- Choose `New app`.
- Select the GitHub repo.
- Set the main file path to `app.py`.
- Deploy.

## If you use Hugging Face Spaces

- Create a new Space.
- Choose the Streamlit template.
- Link the GitHub repo or upload the files.
- Make sure the entry file is `app.py`.
- Deploy.

## What I cannot do for you

- I cannot sign into your Streamlit Cloud or Hugging Face account.
- I cannot create the live hosted URL without your account access.
- I cannot fill in your real email or phone number.
- I cannot verify the sandbox after deployment unless you provide the live URL.

## Final check before submission

- Replace the placeholder contact info in `submission_metadata.yaml`.
- Replace `sandbox_link` with the live URL.
- Confirm the app opens and shows the sample candidate ranking.