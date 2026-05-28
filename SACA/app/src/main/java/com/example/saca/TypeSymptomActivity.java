package com.example.saca;

import android.content.Intent;
import android.graphics.Color;
import android.os.Bundle;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

public class TypeSymptomActivity extends AppCompatActivity {

    String language = "english";
    int    age      = 30;
    String gender   = "";

    EditText symptomInput;
    Button   nextButton;
    TextView backButton, errorText;

    // Keyword map: typed word → canonical symptom name
    private static final String[][] KEYWORD_MAP = {
            {"headache","head pain","migraine","head ache","skull"},                    // → Headache
            {"fever","temperature","hot","feverish","high temp","burning up","pyrexia"},// → Fever
            {"chest","chest pain","heart","cardiac","tight chest","palpitation"},       // → Chest Pain
            {"cough","coughing","dry cough","wet cough"},                               // → Cough
            {"stomach","belly","abdomen","abdominal","nausea","vomit","tummy","gut","gastro","bowel"}, // → Stomach Pain
            {"breath","breathless","breathing","short of breath","wheeze","asthma"},    // → Hard to Breathe
            {"dizzy","dizziness","light head","vertigo","spinning"},                    // → Feeling Dizzy
            {"tired","fatigue","exhausted","weak","no energy","lethargic","weary"},     // → Very Tired
            {"rash","itch","itchy","hives","redness","spots","skin"},                   // → Skin Rash
            {"back","back pain","spine","lower back","upper back","backache"},          // → Back Pain
            {"throat","sore throat","swallowing","tonsil","strep"},                     // → Sore Throat
            {"vomit","vomiting","throwing up","throw up"},                              // → Vomiting
            // Yolŋu Matha keywords
            {"märr","marr","fever yolŋu"},                                              // → Fever
            {"ŋuthu","nuthu","headache yolngu"},                                        // → Headache
            {"buku","birrka","chest yolngu"},                                           // → Chest Pain
            {"wäŋa","wana","stomach yolngu"},                                           // → Stomach Pain
            {"gälk","galk","back yolngu"},                                              // → Back Pain
            {"dhäwu","dhawu","throat yolngu"},                                          // → Sore Throat
    };

    private static final String[] SYMPTOM_NAMES = {
            "Headache", "Fever", "Chest Pain", "Cough", "Stomach Pain",
            "Hard to Breathe", "Feeling Dizzy", "Very Tired", "Skin Rash",
            "Back Pain", "Sore Throat", "Vomiting",
            "Fever", "Headache", "Chest Pain", "Stomach Pain", "Back Pain", "Sore Throat"
    };

    private static final String[] BODY_PARTS = {
            "Head", "Whole Body", "Chest", "Chest", "Stomach",
            "Chest", "Head", "Whole Body", "Whole Body",
            "Back", "Throat", "Stomach",
            "Whole Body", "Head", "Chest", "Stomach", "Back", "Throat"
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_type_symptom);

        language = getIntent().getStringExtra("language");
        age      = getIntent().getIntExtra("age", 30);
        gender   = getIntent().getStringExtra("gender");
        if (language == null) language = "english";
        if (gender == null)   gender   = "";

        backButton   = findViewById(R.id.backButton);
        symptomInput = findViewById(R.id.symptomInput);
        nextButton   = findViewById(R.id.nextButton);
        errorText    = findViewById(R.id.errorText);

        backButton.setText(AppLanguage.back(language));
        backButton.setOnClickListener(v -> finish());

        nextButton.setText(AppLanguage.next(language));
        nextButton.setOnClickListener(v -> handleNext());
    }

    private void handleNext() {
        String input = symptomInput.getText().toString().trim();

        if (input.isEmpty()) {
            errorText.setText(AppLanguage.isYolngu(language)
                    ? "Dhäwu nhäma maḻŋ'marama" : "Please type your symptom first");
            errorText.setTextColor(Color.parseColor("#EF5350"));
            return;
        }

        String matchedSymptom = matchSymptom(input);
        String matchedBodyPart;

        if (matchedSymptom == null) {
            // Could not identify — pass raw input as symptom
            matchedSymptom  = input;
            matchedBodyPart = "Whole Body";
        } else {
            int idx = getSymptomIndex(matchedSymptom);
            matchedBodyPart = (idx >= 0 && idx < BODY_PARTS.length) ? BODY_PARTS[idx] : "Whole Body";
        }

        errorText.setText("");

        Intent intent = new Intent(TypeSymptomActivity.this, TypedQuestionsActivity.class);
        intent.putExtra("language", language);
        intent.putExtra("symptom",  matchedSymptom);
        intent.putExtra("bodyPart", matchedBodyPart);
        intent.putExtra("age",      age);
        intent.putExtra("gender",   gender);
        startActivity(intent);
    }

    private String matchSymptom(String text) {
        String lower = text.toLowerCase().trim();
        for (int i = 0; i < KEYWORD_MAP.length; i++) {
            for (String kw : KEYWORD_MAP[i]) {
                if (lower.contains(kw)) return SYMPTOM_NAMES[i];
            }
        }
        return null;
    }

    private int getSymptomIndex(String name) {
        for (int i = 0; i < SYMPTOM_NAMES.length; i++) {
            if (SYMPTOM_NAMES[i].equals(name)) return i;
        }
        return -1;
    }
}