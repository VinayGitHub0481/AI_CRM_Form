



function SentimentSection({ formData }) {
  const sentiments = ["positive", "neutral", "negative"];

  return (
    <div className="bg-white shadow rounded-lg p-6">

      <h2 className="text-xl font-bold text-gray-800 border-b pb-2 mb-4">
        HCP Sentiment
      </h2>

      <div className="space-y-3">

        {sentiments.map((sentiment) => (

          <label
            key={sentiment}
            className={`flex items-center gap-3 p-3 rounded-lg border transition-all
              ${
                formData.sentiment === sentiment
                  ? "border-blue-500 bg-blue-50"
                  : "border-gray-200 bg-gray-50"
              }`}
          >

            <input
              type="radio"
              checked={formData.sentiment === sentiment}
              readOnly
              disabled
              className="h-4 w-4 cursor-not-allowed"
            />

            <span
              className={`font-medium ${
                formData.sentiment === sentiment
                  ? "text-blue-700"
                  : "text-gray-600"
              }`}
            >
              {sentiment}
            </span>

          </label>

        ))}

      </div>

      {!formData.sentiment && (
        <p className="mt-4 text-sm italic text-gray-500">
          AI will determine the HCP sentiment after analyzing the conversation.
        </p>
      )}

    </div>
  );
}

export default SentimentSection;
