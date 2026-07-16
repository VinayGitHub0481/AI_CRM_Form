

function InteractionDetails({ formData }) {

  console.log(formData);
  return (
    <div className="bg-white shadow rounded-lg p-6 space-y-5">

      <h2 className="text-xl font-bold text-gray-800 border-b pb-2">
        Interaction Details
      </h2>

      {/* HCP Name */}
      <div>
        <label className="block text-sm font-medium text-gray-600 mb-1">
          HCP Name
        </label>

        <input
          type="text"
          value={formData.hcpName }
          readOnly
          placeholder="HCP Name"
          className="w-full border rounded-lg p-3 bg-gray-100 text-gray-700 cursor-not-allowed"
        />
      </div>

      {/* Interaction Type */}
      <div>
        <label className="block text-sm font-medium text-gray-600 mb-1">
          Interaction Type
        </label>

        <input
          type="text"
          value={formData.interactionType }
          readOnly
          placeholder="Interaction Type"
          className="w-full border rounded-lg p-3 bg-gray-100 text-gray-700 cursor-not-allowed"
        />
      </div>

      {/* Date & Time */}

      <div className="grid grid-cols-2 gap-4">

        <div>
          <label className="block text-sm font-medium text-gray-600 mb-1">
            Date
          </label>

          <input
            type="text"
            value={formData.date}
            readOnly
            placeholder="YYYY-MM-DD"
            className="w-full border rounded-lg p-3 bg-gray-100 text-gray-700 cursor-not-allowed"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-600 mb-1">
            Time
          </label>

          <input
            type="text"
            value={formData.time}
            readOnly
            placeholder="HH:MM"
            className="w-full border rounded-lg p-3 bg-gray-100 text-gray-700 cursor-not-allowed"
          />
        </div>

      </div>

      {/* Attendees */}

      <div>

        <label className="block text-sm font-medium text-gray-600 mb-1">
          Attendees
        </label>

        <textarea
          rows={2}
          value={formData?.attendees?.join(", ") ?? ""}
          readOnly
          placeholder="attendees"
          className="w-full border rounded-lg p-3 bg-gray-100 resize-none text-gray-700 cursor-not-allowed"
        />

      </div>

      {/* Topics Discussed */}

      <div>

        <label className="block text-sm font-medium text-gray-600 mb-1">
          Topics Discussed
        </label>

        <textarea
          rows={5}
          value={
            Array.isArray(formData?.topicsDiscussed)?
            formData.topicsDiscussed.join("\n"):
            formData?.topicsDiscussed || ""
          }
          readOnly
          placeholder="topics"
          className="w-full border rounded-lg p-3 bg-gray-100 resize-none text-gray-700 cursor-not-allowed"
        />

      </div>

    </div>
  );
}

export default InteractionDetails;

