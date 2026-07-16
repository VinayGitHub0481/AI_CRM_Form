



function FollowUpBox({ followUp }) {
  return (
    <div className="bg-white shadow rounded-lg p-6">

      <h2 className="text-xl font-bold text-gray-800 border-b pb-2 mb-4">
        AI Recommended Follow-up
      </h2>

        <div className="space-y-5">

          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">
              Follow-up Required
            </label>

            <input
              type="text"
              value={followUp.required ? "yes": "no"}
              readOnly
              className="w-full border rounded-lg p-3 bg-gray-100 text-gray-700 cursor-allowed"
            />
          </div>

          {/* Follow-up Date */}

          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">
              Recommended Date
            </label>

            <input
              type="text"
              value={followUp?.date ?? ""}
              readOnly
              placeholder="AI will determine the follow-up date"
              className="w-full border rounded-lg p-3 bg-gray-100 text-gray-700 cursor-not-allowed"
            />
          </div>

          {/* Follow-up Purpose */}

          <div>
            <label className="block text-sm font-medium text-gray-600 mb-1">
              Purpose
            </label>

            <textarea
              rows={4}
              value={followUp?.purpose ?? ""}
              readOnly
              placeholder="AI will determine the follow-up purpose"
              className="w-full border rounded-lg p-3 bg-gray-100 text-gray-700 resize-none cursor-not-allowed focus:outline-none"
            />
          </div>

        </div>

    </div>
  );
}

export default FollowUpBox;


