package com.example.saca;

import android.content.Intent;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

public class QuestionsActivity extends AppCompatActivity {

    String language = "english";
    String bodyPart = "";
    String symptom  = "";
    String symptomKey = "";
    int    age      = 30;
    String gender   = "";

    TextView backButton, questionCount, questionTitle, questionSub, symptomChip;
    TextView option1, option2, option3, option4, option5, option6;
    LinearLayout card1, card2, card3, card4, card5, card6;
    Button nextButton;

    int questionNo     = 1;
    int selectedOption = 0;
    int totalScore     = 0;

    // Per-question stored answers for result screen
    int ansWhen = 1, ansSev = 5, ansFever = 1, ansBreath = 1, ansDizzy = 1, ansAct = 1;

    // Desktop-exact question data
    // When: 4 options
    static final String[][] WHEN_OPTS = {
        {"📅\nToday",          "#4ADE80"},
        {"🗓️\nYesterday",      "#60A5FA"},
        {"⏳\n2–7 days",       "#FB923C"},
        {"📆\nOver a week",    "#EF4444"},
    };
    // Severity: 6 options — face cards
    static final String[][] SEV_OPTS = {
        {"😊\n1\nVery Mild",   "#4ADE80"},
        {"🙂\n3\nMild",        "#A3E635"},
        {"😐\n5\nModerate",    "#FCD34D"},
        {"😣\n7\nSevere",      "#FB923C"},
        {"😫\n9\nV.Severe",    "#EF4444"},
        {"😵\n10\nExtreme",    "#D32F2F"},
    };
    // Fever: 4 options — exact from desktop
    static final String[][] FEVER_OPTS = {
        {"🟢🌡\nNo fever\nI feel normal",          "#4ADE80"},
        {"🟡🌡\nWarm\nBody feels a bit hot",        "#FCD34D"},
        {"🟠🌡\nFever\nClearly feverish",           "#FB923C"},
        {"🔴🌡\nHigh fever\nVery hot / burning",   "#EF4444"},
    };
    // Breathing: 6 options — exact from desktop
    static final String[][] BREATH_OPTS = {
        {"😊\n1\nFine",        "#4ADE80"},
        {"🙂\n3\nSlight",      "#A3E635"},
        {"😐\n5\nModerate",    "#FCD34D"},
        {"😣\n7\nDifficult",   "#FB923C"},
        {"😫\n9\nVery hard",   "#EF4444"},
        {"😵\n10\nCannot",     "#D32F2F"},
    };
    // Sick/Dizzy: 4 options
    static final String[][] DIZZY_OPTS = {
        {"✓\nNo\nFeeling OK",                "#4ADE80"},
        {"~\nSick stomach\nNausea/vomiting", "#FCD34D"},
        {"!\nDizzy\nSpinning or faint",      "#FB923C"},
        {"✗\nBoth\nSick AND dizzy",          "#EF4444"},
    };
    // Daily activity: 4 options — exact from desktop
    static final String[][] ACT_OPTS = {
        {"✓\nYes, fully\nDoing everything normally",    "#4ADE80"},
        {"~\nMostly yes\nSlowing down a little",        "#FCD34D"},
        {"!\nStruggling\nHard to eat, walk or move",    "#FB923C"},
        {"✗\nNo, cannot\nLying down, need help",        "#EF4444"},
    };

    // Yolngu question subtitles — exact from desktop
    static final String[] YO_SUBS = {
        "Nhaltjan warray ga djäma?",
        "Tap the face that matches  ·  1 = Märr   10 = Ganydjarr",
        "Rumbal nhirrpan?  ·  Is your body hot?",
        "1 = Ŋamak  ·  10 = Wakal djorra'",
        "Nausea · Dizzy · Ŋunhi?",
        "Maḏakarr · Ŋatha · Dhäwu nhakun?",
    };
    static final String[] EN_SUBS = {
        "Tap the best answer  ·  Nhaltjan warray ga djäma?",
        "Tap the face that matches  ·  1 = Very mild   10 = Very bad",
        "Is your body hot?  ·  Do you feel hotter than normal?",
        "1 = Fine  ·  10 = Cannot breathe at all",
        "Nausea · Vomiting · Spinning · Light-headed",
        "Eating  ·  Walking  ·  Looking after yourself  ·  Normal life",
    };
    static final String[] EN_TITLES = {
        "When did it start? 📅",
        "How bad does it feel? 😣",
        "Do you have a fever? 🌡",
        "Can you breathe OK? 💨",
        "Feeling sick or dizzy? 🤢",
        "Can you do daily activities? 🚶",
    };
    static final String[] YO_TITLES = {
        "Ŋunhi dhu gaḏayka? 📅",
        "Nhaltjan ŋoy? 😣",
        "Fever ŋarra? 🌡",
        "Breathing OK? 💨",
        "Sick ga dizzy? 🤢",
        "Daily work OK? 🚶",
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_questions);

        language   = getIntent().getStringExtra("language");
        bodyPart   = getIntent().getStringExtra("bodyPart");
        symptom    = getIntent().getStringExtra("symptom");
        symptomKey = getIntent().getStringExtra("symptomKey");
        age        = getIntent().getIntExtra("age", 30);
        gender     = getIntent().getStringExtra("gender");
        if (language   == null) language   = "english";
        if (bodyPart   == null) bodyPart   = "General";
        if (symptom    == null) symptom    = "Symptom";
        if (symptomKey == null) symptomKey = "fever";
        if (gender     == null) gender     = "";

        backButton   = findViewById(R.id.backButton);
        questionCount= findViewById(R.id.questionNumber);
        questionTitle= findViewById(R.id.questionTitle);
        questionSub  = findViewById(R.id.questionSub);
        symptomChip  = findViewById(R.id.symptomChip);
        card1 = findViewById(R.id.card1); option1 = findViewById(R.id.option1);
        card2 = findViewById(R.id.card2); option2 = findViewById(R.id.option2);
        card3 = findViewById(R.id.card3); option3 = findViewById(R.id.option3);
        card4 = findViewById(R.id.card4); option4 = findViewById(R.id.option4);
        card5 = findViewById(R.id.card5); option5 = findViewById(R.id.option5);
        card6 = findViewById(R.id.card6); option6 = findViewById(R.id.option6);
        nextButton = findViewById(R.id.nextButton);

        backButton.setText(AppLanguage.back(language));
        backButton.setOnClickListener(v -> {
            if (questionNo > 1) { questionNo--; selectedOption = 0; loadQuestion(); }
            else finish();
        });

        // Show symptom name on chip
        symptomChip.setText(symptom);

        card1.setOnClickListener(v -> selectOption(1));
        card2.setOnClickListener(v -> selectOption(2));
        card3.setOnClickListener(v -> selectOption(3));
        card4.setOnClickListener(v -> selectOption(4));
        card5.setOnClickListener(v -> selectOption(5));
        card6.setOnClickListener(v -> selectOption(6));

        loadQuestion();

        nextButton.setOnClickListener(v -> {
            if (selectedOption == 0) {
                Toast.makeText(this,
                    AppLanguage.isYolngu(language) ? "Nhäma maḻŋ'marama" : "Please select an answer",
                    Toast.LENGTH_SHORT).show();
                return;
            }
            recordAnswer();
            totalScore += scoreQuestion(questionNo, selectedOption);
            if (questionNo < 6) {
                questionNo++; selectedOption = 0; loadQuestion();
            } else {
                goToResult();
            }
        });
    }

    private void loadQuestion() {
        resetCards();
        card5.setVisibility(View.GONE);
        card6.setVisibility(View.GONE);

        boolean yo = AppLanguage.isYolngu(language);
        questionCount.setText("Question " + questionNo + " of 6");
        questionTitle.setText(yo ? YO_TITLES[questionNo-1] : EN_TITLES[questionNo-1]);
        questionSub.setText(yo   ? YO_SUBS[questionNo-1]   : EN_SUBS[questionNo-1]);

        String[][] opts;
        switch (questionNo) {
            case 1:  opts = WHEN_OPTS;   break;
            case 2:  opts = SEV_OPTS;    card5.setVisibility(View.VISIBLE); card6.setVisibility(View.VISIBLE); break;
            case 3:  opts = FEVER_OPTS;  break;
            case 4:  opts = BREATH_OPTS; card5.setVisibility(View.VISIBLE); card6.setVisibility(View.VISIBLE); break;
            case 5:  opts = DIZZY_OPTS;  break;
            default: opts = ACT_OPTS;
                nextButton.setText(AppLanguage.analyse(language));
                nextButton.setBackgroundTintList(
                    android.content.res.ColorStateList.valueOf(Color.parseColor("#FF6B35")));
                break;
        }

        TextView[] textViews = {option1, option2, option3, option4, option5, option6};
        for (int i = 0; i < opts.length && i < 6; i++) {
            textViews[i].setText(opts[i][0]);
        }
    }

    private void selectOption(int opt) {
        selectedOption = opt;
        resetCards();

        LinearLayout[] cards  = {card1, card2, card3, card4, card5, card6};
        TextView[]     texts  = {option1, option2, option3, option4, option5, option6};

        String[][] opts;
        switch (questionNo) {
            case 1: opts = WHEN_OPTS;   break;
            case 2: opts = SEV_OPTS;    break;
            case 3: opts = FEVER_OPTS;  break;
            case 4: opts = BREATH_OPTS; break;
            case 5: opts = DIZZY_OPTS;  break;
            default: opts = ACT_OPTS;   break;
        }

        int idx = opt - 1;
        if (idx < opts.length) {
            GradientDrawable bg = new GradientDrawable();
            bg.setColor(Color.parseColor(opts[idx][1]));
            bg.setCornerRadius(44f);
            cards[idx].setBackground(bg);
            texts[idx].setTextColor(Color.WHITE);
        }
    }

    private void resetCards() {
        LinearLayout[] cards = {card1, card2, card3, card4, card5, card6};
        TextView[]     texts = {option1, option2, option3, option4, option5, option6};
        for (int i = 0; i < 6; i++) {
            cards[i].setBackgroundResource(R.drawable.question_card);
            texts[i].setTextColor(Color.parseColor("#132238"));
        }
        if (questionNo != 6) {
            nextButton.setText(AppLanguage.next(language));
            nextButton.setBackgroundTintList(
                android.content.res.ColorStateList.valueOf(Color.parseColor("#4ADE80")));
        }
    }

    private void recordAnswer() {
        switch (questionNo) {
            case 1: ansWhen   = selectedOption; break;
            case 2: ansSev    = selectedOption; break;
            case 3: ansFever  = selectedOption; break;
            case 4: ansBreath = selectedOption; break;
            case 5: ansDizzy  = selectedOption; break;
            case 6: ansAct    = selectedOption; break;
        }
    }

    // Scoring matching desktop triage.py _rule_based()
    private int scoreQuestion(int q, int opt) {
        switch (q) {
            case 1: return opt;                     // onset: 1–4 days
            case 2: return opt * 2;                 // severity 1–10 × 2
            case 3: return (opt - 1) * 2;           // fever: none=0, warm=2, fever=4, high=6
            case 4: return opt * 3;                 // breathing most critical × 3
            case 5: return (opt - 1) * 2;           // dizzy: no=0, sick=2, dizzy=4, both=6
            case 6: return (5 - opt) * 2;           // activity inverted: fully=0, cannot=8
            default: return 0;
        }
    }

    private void goToResult() {
        // Thresholds matching desktop: severe≥20, moderate≥11
        String severity;
        if      (totalScore >= 20) severity = "SEVERE";
        else if (totalScore >= 11) severity = "MODERATE";
        else                       severity = "MILD";

        String[] whenLabels   = {"", "Today",     "Yesterday",  "2–7 days",  "Over a week"};
        String[] sevLabels    = {"", "1-Very Mild","3-Mild",     "5-Moderate","7-Severe","9-V.Severe","10-Extreme"};
        String[] feverLabels  = {"", "No fever",  "Warm",       "Fever",     "High fever"};
        String[] breathLabels = {"", "Fine",      "Slight",     "Moderate",  "Difficult","Very hard","Cannot"};
        String[] dizzyLabels  = {"", "No",        "Sick stomach","Dizzy",    "Both"};
        String[] actLabels    = {"", "Yes, fully","Mostly yes", "Struggling","Cannot"};

        Intent intent = new Intent(QuestionsActivity.this, ResultActivity.class);
        intent.putExtra("language",    language);
        intent.putExtra("bodyPart",    bodyPart);
        intent.putExtra("symptom",     symptom);
        intent.putExtra("severity",    severity);
        intent.putExtra("score",       totalScore);
        intent.putExtra("age",         age);
        intent.putExtra("gender",      gender);
        intent.putExtra("ansWhen",      safe(whenLabels,   ansWhen));
        intent.putExtra("ansSeverity",  safe(sevLabels,    ansSev));
        intent.putExtra("ansFever",     safe(feverLabels,  ansFever));
        intent.putExtra("ansBreathing", safe(breathLabels, ansBreath));
        intent.putExtra("ansDizzy",     safe(dizzyLabels,  ansDizzy));
        intent.putExtra("ansActivity",  safe(actLabels,    ansAct));
        startActivity(intent);
    }

    private String safe(String[] arr, int i) {
        return (i >= 0 && i < arr.length) ? arr[i] : "—";
    }
}
