package com.example.saca;

import android.content.Intent;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.speech.RecognizerIntent;
import android.view.View;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import java.util.ArrayList;
import java.util.Locale;

public class SpeakQuestionsActivity extends AppCompatActivity {

    String language = "english";
    int age = 30;
    String gender = "";

    TextView backButton, questionCount, questionTitle, questionSub;
    TextView answerText, statusText;
    Button micButton, nextButton;

    int currentQuestion = 0;
    final int SPEECH_CODE = 200;
    String currentAnswer = "";
    int totalScore = 0;

    // Store raw answers for result screen
    String[] storedAnswers = new String[6];

    String[] englishQuestions = {
            "When did it start?",
            "How bad does it feel? (1 to 10)",
            "Do you have a fever?",
            "Can you breathe normally?",
            "Feeling sick or dizzy?",
            "Can you do daily activities?"
    };

    String[] englishSubs = {
            "Say: today / yesterday / a few days / over a week",
            "Say a number from 1 (very mild) to 10 (extreme)",
            "Say: no fever / warm / fever / high fever",
            "Say: fine / slight / moderate / difficult / cannot breathe",
            "Say: no / sick stomach / dizzy / both",
            "Say: yes fully / mostly / struggling / cannot"
    };

    String[] yolnguQuestions = {
            "Ŋunhi dhu gaḏayka?",
            "Nhaltjan ŋoy? (1 ga 10)",
            "Fever ŋarra?",
            "Breathing OK?",
            "Sick ga dizzy?",
            "Daily work OK?"
    };

    String[] yolnguSubs = {
            "Waŋa: bayŋu / warray / ŋärra / week",
            "Waŋa namba 1 ga 10",
            "Waŋa: no fever / warm / fever / high fever",
            "Waŋa: fine / slight / hard / cannot",
            "Waŋa: no / sick / dizzy / both",
            "Waŋa: yes / mostly / struggling / cannot"
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_speak_questions);

        language = getIntent().getStringExtra("language");
        age      = getIntent().getIntExtra("age", 30);
        gender   = getIntent().getStringExtra("gender");
        if (language == null) language = "english";
        if (gender == null)   gender   = "";

        backButton    = findViewById(R.id.backButton);
        questionCount = findViewById(R.id.questionCount);
        questionTitle = findViewById(R.id.questionText);
        questionSub   = findViewById(R.id.questionSub);
        answerText    = findViewById(R.id.answerText);
        statusText    = findViewById(R.id.statusText);
        micButton     = findViewById(R.id.micButton);
        nextButton    = findViewById(R.id.nextButton);

        backButton.setText(AppLanguage.back(language));
        backButton.setOnClickListener(v -> {
            if (currentQuestion > 0) { currentQuestion--; currentAnswer = ""; loadQuestion(); }
            else finish();
        });

        micButton.setOnClickListener(v -> startSpeech());
        nextButton.setOnClickListener(v -> handleNext());

        loadQuestion();
    }

    private void loadQuestion() {
        boolean yo = AppLanguage.isYolngu(language);
        questionCount.setText("Question " + (currentQuestion + 1) + " of 6");
        questionTitle.setText(yo ? yolnguQuestions[currentQuestion] : englishQuestions[currentQuestion]);
        questionSub.setText(yo   ? yolnguSubs[currentQuestion]      : englishSubs[currentQuestion]);

        answerText.setText(yo ? "🎤  Tap mic ga speak" : "🎤  Tap the microphone and speak");
        answerText.setTextColor(Color.parseColor("#6C8DB5"));
        if (statusText != null) statusText.setText("");

        currentAnswer = "";

        if (currentQuestion == 5) {
            nextButton.setText(AppLanguage.analyse(language));
            nextButton.setBackgroundTintList(
                    android.content.res.ColorStateList.valueOf(Color.parseColor("#FF6B35")));
        } else {
            nextButton.setText(AppLanguage.next(language));
            nextButton.setBackgroundTintList(
                    android.content.res.ColorStateList.valueOf(Color.parseColor("#1685D9")));
        }
    }

    private void handleNext() {
        if (currentAnswer.isEmpty()) {
            Toast.makeText(this,
                    AppLanguage.isYolngu(language)
                            ? "Mic guŋga' waŋa djäma" : "Please speak your answer first",
                    Toast.LENGTH_SHORT).show();
            return;
        }

        storedAnswers[currentQuestion] = currentAnswer;
        totalScore += scoreAnswer(currentQuestion, currentAnswer);
        currentQuestion++;
        currentAnswer = "";

        if (currentQuestion < englishQuestions.length) {
            loadQuestion();
        } else {
            goToResult();
        }
    }

    private void startSpeech() {
        Intent intent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, Locale.getDefault());
        intent.putExtra(RecognizerIntent.EXTRA_PROMPT,
                AppLanguage.isYolngu(language) ? "Waŋa answer" : "Speak your answer");
        try {
            startActivityForResult(intent, SPEECH_CODE);
        } catch (Exception e) {
            Toast.makeText(this, "Speech input not available on this device", Toast.LENGTH_SHORT).show();
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == SPEECH_CODE && resultCode == RESULT_OK && data != null) {
            ArrayList<String> results = data.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS);
            if (results != null && !results.isEmpty()) {
                currentAnswer = results.get(0);
                answerText.setText("✓  \"" + currentAnswer + "\"");
                answerText.setTextColor(Color.parseColor("#009B72"));
            }
        }
    }

    /**
     * Keyword-based scoring — mirrors Python s4_questions_voice._interpret()
     */
    private int scoreAnswer(int question, String answer) {
        String t = answer.toLowerCase().trim();
        switch (question) {
            case 0: // when
                if (contains(t,"today","now","just","morning"))     return 1;
                if (contains(t,"yesterday","one day","1 day"))      return 2;
                if (contains(t,"two","three","few","couple","2","3"))return 3;
                if (contains(t,"week","seven","4","5","6","7"))      return 4;
                return 2;

            case 1: // severity
                try {
                    int n = extractNumber(t);
                    if (n >= 1 && n <= 10) return n * 2;
                } catch (Exception ignored) {}
                if (contains(t,"mild","low","light","little")) return 2;
                if (contains(t,"moderate","okay","medium"))    return 6;
                if (contains(t,"severe","bad","very bad"))     return 14;
                if (contains(t,"extreme","worst","terrible"))  return 20;
                return 6;

            case 2: // fever
                if (contains(t,"high fever","very hot","burning","40","41")) return 8;
                if (contains(t,"fever","feverish","hot","38","39"))          return 6;
                if (contains(t,"warm","bit warm","37"))                      return 2;
                if (contains(t,"no fever","no","normal","fine"))             return 0;
                return 2;

            case 3: // breathing  ← most critical
                if (contains(t,"cannot","can't","no breath","worst")) return 18;
                if (contains(t,"very hard","really hard","struggling")) return 12;
                if (contains(t,"moderate","some","difficult"))          return 9;
                if (contains(t,"slight","little","mild"))               return 6;
                if (contains(t,"fine","normal","okay","breathing well"))return 0;
                return 3;

            case 4: // sick/dizzy
                if (contains(t,"both","sick and dizzy","nausea and dizzy")) return 8;
                if (contains(t,"dizzy","dizziness","faint","spinning"))     return 6;
                if (contains(t,"sick","nausea","vomit","queasy"))           return 4;
                if (contains(t,"no","not","fine","nothing","neither"))      return 0;
                return 2;

            case 5: // daily activity (inverted — cannot = worst)
                if (contains(t,"cannot","can't","bed","lying","help"))     return 8;
                if (contains(t,"struggling","hard","barely","difficult"))  return 6;
                if (contains(t,"mostly","sort of","some","little","okay")) return 4;
                if (contains(t,"yes","fully","normal","fine","all"))       return 0;
                return 4;

            default: return 0;
        }
    }

    private boolean contains(String text, String... keywords) {
        for (String kw : keywords) if (text.contains(kw)) return true;
        return false;
    }

    private int extractNumber(String text) {
        for (String token : text.split("\\s+")) {
            try { return Integer.parseInt(token.replaceAll("[^0-9]","")); }
            catch (Exception ignored) {}
        }
        throw new RuntimeException("no number");
    }

    private void goToResult() {
        String severity;
        if      (totalScore <= 18) severity = "MILD";
        else if (totalScore <= 36) severity = "MODERATE";
        else                       severity = "SEVERE";

        Intent intent = new Intent(SpeakQuestionsActivity.this, ResultActivity.class);
        intent.putExtra("language",    language);
        intent.putExtra("severity",    severity);
        intent.putExtra("score",       totalScore);
        intent.putExtra("age",         age);
        intent.putExtra("gender",      gender);
        for (int i = 0; i < storedAnswers.length; i++) {
            intent.putExtra("ans" + i, storedAnswers[i] != null ? storedAnswers[i] : "—");
        }
        startActivity(intent);
    }
}