package com.example.saca;

import android.content.Intent;
import android.os.Bundle;
import android.text.InputType;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatActivity;

public class TypedQuestionsActivity extends AppCompatActivity {

    String language = "english";
    String symptom  = "";
    String bodyPart = "";
    int    age      = 30;
    String gender   = "";

    TextView questionNumber, questionText, questionHint, errorText, backButton;
    EditText answerInput;
    Button nextButton;

    int currentQuestion = 2;

    String[] englishQuestions = {
            "Where is the symptom?",
            "How long have you had this symptom?",
            "How bad is the pain or discomfort?",
            "Do you have any other symptoms?",
            "Have you taken any medicine?"
    };
    String[] englishHints = {
            "e.g. head / throat / chest / stomach / back",
            "e.g. today / yesterday / 2 days / a week / longer",
            "Type a number from 1 (very mild) to 10 (worst possible)",
            "e.g. vomiting / dizziness / chills / hard to breathe / none",
            "e.g. Panadol / paracetamol / antibiotics / nothing"
    };
    String[] yolnguQuestions = {
            "Wanha symptom?",
            "Nhaltjan ŋärra symptom?",
            "Pain nhaltjan? (1 ga 10)",
            "Other symptoms?",
            "Medicine ŋarra?"
    };
    String[] yolnguHints = {
            "e.g. head / throat / chest / stomach / back",
            "e.g. bayŋu / warray / 2 ŋärra / week / longer",
            "Type 1 to 10",
            "e.g. vomiting / dizzy / chills / breathe hard / none",
            "e.g. Panadol / nothing"
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_typed_questions);

        language = getIntent().getStringExtra("language");
        symptom  = getIntent().getStringExtra("symptom");
        bodyPart = getIntent().getStringExtra("bodyPart");
        age      = getIntent().getIntExtra("age", 30);
        gender   = getIntent().getStringExtra("gender");
        if (language == null) language = "english";
        if (symptom  == null) symptom  = "";
        if (bodyPart == null) bodyPart = "Whole Body";
        if (gender   == null) gender   = "";

        backButton     = findViewById(R.id.backButton);
        questionNumber = findViewById(R.id.questionNumber);
        questionText   = findViewById(R.id.questionText);
        questionHint   = findViewById(R.id.questionHint);
        errorText      = findViewById(R.id.errorText);
        answerInput    = findViewById(R.id.answerInput);
        nextButton     = findViewById(R.id.nextButton);

        backButton.setText(AppLanguage.back(language));
        backButton.setOnClickListener(v -> {
            if (currentQuestion > 2) {
                currentQuestion--;
                answerInput.setText("");
                errorText.setText("");
                loadQuestion();
            } else {
                finish();
            }
        });

        loadQuestion();

        nextButton.setOnClickListener(v -> {
            String answer = answerInput.getText().toString().trim();

            if (answer.isEmpty()) {
                errorText.setText(AppLanguage.isYolngu(language)
                        ? "Dhäruk nhäma maḻŋ'marama" : "Please type your answer");
                return;
            }

            // Validate severity (Q4)
            if (currentQuestion == 4) {
                try {
                    int n = Integer.parseInt(answer);
                    if (n < 1 || n > 10) {
                        errorText.setText(AppLanguage.isYolngu(language)
                                ? "Type 1 to 10" : "Please type a number between 1 and 10");
                        return;
                    }
                } catch (Exception e) {
                    errorText.setText(AppLanguage.isYolngu(language)
                            ? "Type 1 to 10" : "Please type a number between 1 and 10");
                    return;
                }
            }

            currentQuestion++;
            answerInput.setText("");
            errorText.setText("");

            if (currentQuestion <= 6) {
                loadQuestion();
            } else {
                // ✅ FIXED: Route to QuestionsActivity (tap-card questions)
                // NOT directly to ResultActivity — matches desktop flow
                Intent intent = new Intent(TypedQuestionsActivity.this, QuestionsActivity.class);
                intent.putExtra("language", language);
                intent.putExtra("symptom",  symptom.isEmpty() ? "Symptom" : symptom);
                intent.putExtra("bodyPart", bodyPart);
                intent.putExtra("age",      age);
                intent.putExtra("gender",   gender);
                startActivity(intent);
            }
        });
    }

    private void loadQuestion() {
        int index = currentQuestion - 2;
        boolean yo = AppLanguage.isYolngu(language);

        questionNumber.setText("Question " + currentQuestion + " of 6");
        questionText.setText(yo ? yolnguQuestions[index] : englishQuestions[index]);
        questionHint.setText(yo ? yolnguHints[index]     : englishHints[index]);

        answerInput.setInputType(currentQuestion == 4
                ? InputType.TYPE_CLASS_NUMBER : InputType.TYPE_CLASS_TEXT);

        if (currentQuestion == 6) {
            nextButton.setText(AppLanguage.next(language));
        } else {
            nextButton.setText(AppLanguage.next(language));
        }
    }
}