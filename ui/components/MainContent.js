"use client";

import { useState } from "react";

const DEFAULT_PROMPT = `كوميكس ملوّن بأسلوب مانغا/أنمي مرح وخفيف. المشهد في شارع قديم ليلًا، إضاءة فوانيس بسيطة.
هارون الرشيد يظهر بملامح وقار مع لمسة استغراب، حاجب مرفوع ونظرة فاحصة. رجل بسيط يحمل زجاجة خمر، ملامحه ذكية وماكرة قليلًا.
الكوميكس مكوّن من ثلاث لوحات واضحة: اللوحة الأولى: هارون الرشيد ينظر إلى الزجاجة ويسأل باستغرب: «ما هذا بيدك؟» اللوحة الثانية:
الرجل يرد بسرعة وبوجه بريء: «هذا لبن». اللوحة الثالثة: هارون الرشيد يقترب قليلًا ويقول متعجبًا: «ومتى أصبح اللبن أحمر يا هذا؟» الرجل يبتسم بثقة ودهاء ويجيب: «احمر خجلًا منك يا أمير المؤمنين» فعجب هارون الرشيد من دهاء الرجل فضحك أمير المؤمنين وعفى عنه.
ألوان دافئة، تعبيرات وجه واضحة ومبالغ فيها قليلًا لإبراز الطرافة، لغة جسد كوميدية، أسلوب كوميكس لطيف، جودة عالية.`;

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
          اكتب القصة باللغة العربية وسيُنشئ الذكاء الاصطناعي صفحة كوميكس.
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <label className="font-medium text-[#1a1a1a] text-[15px]">
            القصة (عربي):
          </label>
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
