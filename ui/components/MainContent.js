"use client";

import { useState } from "react";

const STORY_PRESETS = [
  {
    title: "هارون الرشيد ولبن الأحمر",
    prompt: `كوميكس ملوّن بأسلوب مانغا/أنمي مرح وخفيف. المشهد في شارع قديم ليلًا، إضاءة فوانيس بسيطة.
هارون الرشيد يظهر بملامح وقار مع لمسة استغراب، حاجب مرفوع ونظرة فاحصة. رجل بسيط يحمل زجاجة خمر، ملامحه ذكية وماكرة قليلًا.
الكوميكس مكوّن من ثلاث لوحات واضحة: اللوحة الأولى: هارون الرشيد ينظر إلى الزجاجة ويسأل باستغرب: «ما هذا بيدك؟» اللوحة الثانية:
الرجل يرد بسرعة وبوجه بريء: «هذا لبن». اللوحة الثالثة: هارون الرشيد يقترب قليلًا ويقول متعجبًا: «ومتى أصبح اللبن أحمر يا هذا؟» الرجل يبتسم بثقة ودهاء ويجيب: «احمر خجلًا منك يا أمير المؤمنين» فعجب هارون الرشيد من دهاء الرجل فضحك أمير المؤمنين وعفى عنه.
ألوان دافئة، تعبيرات وجه واضحة ومبالغ فيها قليلًا لإبراز الطرافة، لغة جسد كوميدية، أسلوب كوميكس لطيف، جودة عالية.`
  },
  {
    title: "جحا وحماره الضائع",
    prompt: `كوميكس ملوّن بأسلوب مانغا/أنمي مرح وخفيف. المشهد في طريق ريفي بسيط وقت النهار، خلفية نخيل وأرض ترابية. جحا يظهر بملابس بسيطة وملامح طريفة، جالس على حماره لكن يبدو عليه القلق والبحث. مجموعة رجال حوله ينظرون باستغراب.
الكوميكس مكوّن من ثلاث لوحات واضحة:
اللوحة الأولى: جحا ينظر يمين ويسار بقلق وهو فوق الحمار ويقول: «أين حماري؟ لقد ضاع!»
اللوحة الثانية: أحد الرجال يشير إليه بدهشة ويقول: «أنت راكبه يا جحا!»
اللوحة الثالثة: جحا ينظر للأسفل بصدمة ثم يبتسم براحة ويقول: «الحمد لله، وجدته… كنت قلقًا عليه!»
ألوان دافئة، تعبيرات وجه مبالغ فيها لإبراز الكوميديا، حركة جسد مضحكة، أسلوب كوميكس لطيف، جودة عالية.`
  },
  {
    title: "المريض والأعرابي",
    prompt: `كوميكس ملوّن بأسلوب مانغا/أنمي مرح وخفيف. المشهد داخل غرفة بسيطة في بيت قديم، إضاءة خافتة من مصباح زيتي، أجواء هادئة. رجل مريض مستلقٍ على فراش بملامح متعبة لكنه متكلف في التعبير، يقابله أعرابي بسيط بملامح مباشرة ونظرة مستغربة.
الكوميكس مكوّن من ثلاث لوحات واضحة:
اللوحة الأولى: الأعرابي يقف بجانب الفراش ويسأل بصدق: «ما بك؟»
اللوحة الثانية: المريض يرفع يده بتعب ويتكلم بسجع متكلف: «حمّى جاسية، نارها حامية، منها الأعضاء واهية، والعظام بالية!» مع تعبير درامي مبالغ فيه.
اللوحة الثالثة: الأعرابي ينظر له بنظرة مضحكة ثم يقول ببساطة: «يا ليتها كانت القاضية!» والمريض يتجمد بصدمة خفيفة بوجه مضحك.
ألوان دافئة، تعبيرات وجه واضحة ومبالغ فيها لإبراز المفارقة، تباين بين تعقيد المريض وبساطة الأعرابي، أسلوب كوميكس لطيف ومضحك، جودة عالية.`
  },
  {
    title: "الجاحظ والحمار المثقف",
    prompt: `كوميكس ملوّن بأسلوب مانغا/أنمي مرح وخفيف. المشهد في سوق قديم أو مكتبة بسيطة، رفوف كتب وخلفية تراثية. الجاحظ يظهر بملامح ذكية ونظرة فاحصة، أمامه رجل يحمل كتابًا ضخمًا ويتباهى به.
الكوميكس مكوّن من ثلاث لوحات واضحة:
اللوحة الأولى: الجاحظ ينظر للرجل والكتاب ويقول باستغراب: «هل قرأت هذا الكتاب؟»
اللوحة الثانية: الرجل يبتسم بثقة ويقول: «لا، أحمله ليقال إني مثقف.»
اللوحة الثالثة: الجاحظ يرفع حاجبه بسخرية ويقول: «وهل يحمل الحمار كتبًا فيصبح عالمًا؟» والرجل يتجمد بوجه محرج.
ألوان دافئة، تعبيرات واضحة ومبالغ فيها، طابع ساخر، لغة جسد كوميدية، أسلوب كوميكس لطيف، جودة عالية.`
  }
];

const DEFAULT_PROMPT = STORY_PRESETS[0].prompt;

export default function MainContent({ onGenerate, loading, result, error }) {
  const [prompt, setPrompt] = useState(DEFAULT_PROMPT);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!loading && prompt.trim()) onGenerate(prompt.trim());
  };

  const handleDownload = () => {
    if (!result?.pageBase64) return;
    const link = document.createElement("a");
    link.href = `data:image/png;base64,${result.pageBase64}`;
    link.download = "comic.png";
    link.click();
  };

  return (
    <div className="max-w-2xl mx-auto px-6 py-8">
        <div className="bg-white rounded-xl border border-[#e5e3e0] shadow-sm p-8 mb-8">
        <h1 className="text-2xl font-bold text-[#1a1a1a] mb-2">
          مولد الكوميكس العربي
        </h1>
        <p className="text-[#6b6b6b] mb-8 text-[15px] leading-relaxed">
          اكتب القصة باللغة العربية. تُنشأ لوحات بصرية فقط (بدون نص على الصور)، وتُعرض
          الحوارات أسفل كل لوحة كنص توضيحي.
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <label className="font-medium text-[#1a1a1a] text-[15px]">
            القصة (عربي):
          </label>
          
          {/* Story preset buttons */}
          <div className="flex flex-wrap gap-2">
            {STORY_PRESETS.map((preset, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => setPrompt(preset.prompt)}
                disabled={loading}
                className="px-4 py-2 text-sm border border-[#e5e3e0] rounded-lg bg-[#faf9f7] hover:bg-[#f0efed] active:scale-[0.98] transition-all disabled:opacity-60 disabled:cursor-not-allowed text-[#1a1a1a]"
              >
                {preset.title}
              </button>
            ))}
          </div>

          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="اكتب وصف القصة هنا..."
            className="w-full p-4 border border-[#e5e3e0] rounded-lg text-[15px] resize-y min-h-[180px] focus:outline-none focus:ring-2 focus:ring-[#2563eb] focus:border-transparent transition-shadow disabled:opacity-60 disabled:cursor-not-allowed"
            rows={8}
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading}
            className="self-start px-8 py-3 bg-[#1a1a1a] text-white rounded-lg font-medium hover:bg-[#333] active:scale-[0.98] transition-all disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {loading ? "جاري الإنشاء... (قد يستغرق دقائق)" : "البدء"}
          </button>
        </form>

        {error && (
          <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        )}
      </div>

      {result && (
        <div className="bg-white rounded-xl border border-[#e5e3e0] shadow-sm p-8">
          <h2 className="text-xl font-bold text-[#1a1a1a] mb-6">النتيجة</h2>
          <div className="rounded-lg overflow-hidden border border-[#e5e3e0] bg-[#f5f5f5]">
            <img
              src={`data:image/png;base64,${result.pageBase64}`}
              alt="Comic page"
              className="w-full block"
            />
          </div>
          {Array.isArray(result.script?.panels) && result.script.panels.length > 0 && (
            <div className="mt-8 space-y-6" dir="rtl" lang="ar">
              <h3 className="text-lg font-semibold text-[#1a1a1a]">الحوارات (توضيح لكل لوحة)</h3>
              {result.script.panels.map((panel) => (
                <div
                  key={panel.panel_id}
                  className="rounded-lg border border-[#e5e3e0] bg-[#faf9f7] p-4 text-[15px] leading-relaxed"
                >
                  <p className="font-medium text-[#1a1a1a] mb-2">
                    اللوحة {panel.panel_id}
                  </p>
                  <ul className="space-y-2 text-[#333] list-none m-0 p-0">
                    {(panel.dialogue || []).map((line, idx) => (
                      <li key={idx}>
                        <span className="text-[#6b6b6b]">{line.speaker}:</span>{" "}
                        {line.text_ar}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          )}
          <button
            onClick={handleDownload}
            className="mt-6 px-6 py-2.5 bg-[#1a1a1a] text-white rounded-lg font-medium hover:bg-[#333] active:scale-[0.98] transition-all"
          >
            تحميل الصفحة
          </button>
        </div>
      )}
    </div>
  );
}
