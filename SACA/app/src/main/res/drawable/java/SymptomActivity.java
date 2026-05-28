package com.example.saca;

import android.content.Intent;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.GridLayout;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

public class SymptomActivity extends AppCompatActivity {

    String language = "english";
    String bodyPart = "";
    String selectedSymptom = "";
    String selectedSymptomKey = "";
    int    age    = 30;
    String gender = "";

    TextView backButton, bodyPartText, showMoreBtn;
    GridLayout extraSymptomsGrid;
    Button startQuestionsButton;
    boolean showingAll = false;
    LinearLayout lastSelected = null;

    // All 12 symptoms: {English, Yolngu, emoji, colorHex, key}
    static final String[][] SYMPTOMS = {
        {"Fever",          "Märr",         "🌡", "#E63946", "fever"},
        {"Headache",       "Ŋuthu·ŋuthu",  "🧠", "#6D4C41", "headache"},
        {"Chest Pain",     "Buku·djarrka", "❤",  "#E63946", "chest"},
        {"Stomach Pain",   "Wäŋa·wäŋa",   "🤢", "#F4A261", "stomach"},
        {"Sore Throat",    "Dhäwu",        "🗣", "#FF6B35", "throat"},
        {"Back Pain",      "Gälk",         "🦴", "#C19A6B", "back"},
        // Extra 6
        {"Cough",          "Guku",         "😷", "#1B75BC", "cough"},
        {"Hard to Breathe","Ŋunha",        "💨", "#1B75BC", "breathless"},
        {"Feeling Dizzy",  "Marrtji",      "😵", "#B87333", "dizziness"},
        {"Very Tired",     "Djäka",        "😴", "#8B7355", "fatigue"},
        {"Vomiting",       "Bukmak",       "🤮", "#CD5C5C", "vomiting"},
        {"Skin Rash",      "Ŋuli·ŋuli",    "🔴", "#F4A261", "rash"},
    };

    // Map symptom key → body part
    static final String[] BODY_PARTS = {
        "Whole Body", "Head", "Chest", "Stomach", "Throat", "Back",
        "Chest", "Chest", "Head", "Whole Body", "Stomach", "Whole Body"
    };

    // IDs for the top-6 cards in layout
    int[] topCardIds;
    int[] extraCardIds;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_symptom);

        language = getIntent().getStringExtra("language");
        bodyPart = getIntent().getStringExtra("bodyPart");
        age      = getIntent().getIntExtra("age", 30);
        gender   = getIntent().getStringExtra("gender");
        if (language == null) language = "english";
        if (bodyPart == null) bodyPart = "General";
        if (gender   == null) gender   = "";

        backButton          = findViewById(R.id.backButton);
        bodyPartText        = findViewById(R.id.bodyPartText);
        showMoreBtn         = findViewById(R.id.showMoreBtn);
        extraSymptomsGrid   = findViewById(R.id.extraSymptomsGrid);
        startQuestionsButton= findViewById(R.id.startQuestionsButton);

        backButton.setOnClickListener(v -> finish());
        bodyPartText.setText(
            AppLanguage.isYolngu(language)
                ? "📍 " + bodyPart + " — nhäma dhäruk"
                : "📍 Selected: " + bodyPart);

        // Wire top 6 cards
        int[] topIds = {
            R.id.cardFever, R.id.cardHeadache, R.id.cardChest,
            R.id.cardStomach, R.id.cardThroat, R.id.cardBack
        };
        for (int i = 0; i < 6; i++) {
            final int idx = i;
            LinearLayout card = findViewById(topIds[i]);
            card.setOnClickListener(v -> selectSymptom(card, idx));
        }

        // Wire extra 6 cards
        int[] extraIds = {
            R.id.cardCough, R.id.cardBreath, R.id.cardDizzy,
            R.id.cardTired, R.id.cardVomiting, R.id.cardRash
        };
        for (int i = 0; i < 6; i++) {
            final int idx = i + 6;
            LinearLayout card = findViewById(extraIds[i]);
            card.setOnClickListener(v -> selectSymptom(card, idx));
        }

        // Show more / hide
        showMoreBtn.setOnClickListener(v -> {
            if (!showingAll) {
                extraSymptomsGrid.setVisibility(View.VISIBLE);
                showMoreBtn.setText("▲  Show fewer symptoms");
                showingAll = true;
            } else {
                extraSymptomsGrid.setVisibility(View.GONE);
                showMoreBtn.setText("▼  Show all 12 symptoms");
                showingAll = false;
            }
        });

        // Apply Yolngu labels if needed
        if (AppLanguage.isYolngu(language)) {
            updateLabelsForYolngu(topIds, extraIds);
        }

        startQuestionsButton.setOnClickListener(v -> {
            if (selectedSymptom.isEmpty()) {
                Toast.makeText(this,
                    AppLanguage.isYolngu(language)
                        ? "Dhäruk nhäma maḻŋ'marama"
                        : "Please select a symptom first",
                    Toast.LENGTH_SHORT).show();
                return;
            }
            Intent intent = new Intent(SymptomActivity.this, QuestionsActivity.class);
            intent.putExtra("language", language);
            intent.putExtra("bodyPart", bodyPart);
            intent.putExtra("symptom",  selectedSymptom);
            intent.putExtra("symptomKey", selectedSymptomKey);
            intent.putExtra("age",      age);
            intent.putExtra("gender",   gender);
            startActivity(intent);
        });
    }

    private void selectSymptom(LinearLayout card, int idx) {
        // Reset previous
        if (lastSelected != null) {
            lastSelected.setBackground(getOriginalBackground(lastSelected));
        }
        lastSelected = card;
        selectedSymptom    = SYMPTOMS[idx][0];
        selectedSymptomKey = SYMPTOMS[idx][4];

        // Highlight selected card
        String colorHex = SYMPTOMS[idx][3];
        GradientDrawable sel = new GradientDrawable();
        sel.setColor(Color.parseColor(colorHex));
        sel.setStroke(3, Color.parseColor(colorHex));
        sel.setCornerRadius(24f);
        card.setBackground(sel);

        // Update button colour to match symptom colour
        startQuestionsButton.setBackgroundTintList(
            android.content.res.ColorStateList.valueOf(Color.parseColor(colorHex)));
        startQuestionsButton.setText(
            AppLanguage.isYolngu(language)
                ? "✓  " + SYMPTOMS[idx][1] + "  →"
                : "✓  " + selectedSymptom + "  →");
    }

    private android.graphics.drawable.Drawable getOriginalBackground(LinearLayout card) {
        // Return white card with border
        GradientDrawable def = new GradientDrawable();
        def.setColor(Color.WHITE);
        def.setStroke(2, Color.parseColor("#DDE3F0"));
        def.setCornerRadius(24f);
        return def;
    }

    private void updateLabelsForYolngu(int[] topIds, int[] extraIds) {
        // Update subtitle of each card to show Yolngu name prominently
        // (Cards already have both, just reorder emphasis)
        // This is handled in XML — Yolngu name is always shown as italic subtitle
    }
}
