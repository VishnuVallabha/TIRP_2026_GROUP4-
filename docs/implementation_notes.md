# Swin SACA Prototype - Implementation Notes

## What this prototype demonstrates
- Multilingual symptom intake with a **prototype Yolŋu Matha -> English dictionary layer**.
- Voice input using browser speech recognition for a tutor demonstration.
- Machine-learning-based triage classification into **mild**, **moderate**, and **severe**.
- Website flow that can run locally in VS Code.

## Why Random Forest and XGBoost?
### Random Forest
- Strong baseline for tabular data.
- Easy to explain to a tutor.
- Robust when symptoms interact in non-linear ways.
- Can be less sensitive to noisy features.

### XGBoost
- Often performs very well on structured classification tasks.
- Good for modelling complex feature interactions.
- Efficient and widely used in healthcare/tabular ML prototypes.

## NLP explanation for your tutor
For the current student prototype, the NLP pipeline is:
1. Capture voice or text input.
2. Convert non-English phrases into English using a prototype dictionary.
3. Normalize the translated sentence.
4. Extract known symptoms using a symptom alias matcher.
5. Pass those structured symptoms into the ML model.

This is realistic for a demonstration because it shows the **end-to-end pipeline** even if the final community-scale model would need larger Indigenous language datasets and consultation.

## Important limitation to say clearly
This is a teaching prototype and **not a real clinical device**. It should only be presented as a proof-of-concept decision-support demo.
