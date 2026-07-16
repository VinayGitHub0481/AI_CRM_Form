


function Document({summary}){
return(
    <div className="bg-white shadow rounded-lg p-6">

        <h2 className="text-xl font-bold text-gray-800 border-b pb-2">
            AI Summarized Response
        </h2>

        <div className="mt-4">
            <textarea
              rows={8}
              value={summary || ""}
              readOnly 
              placeholder="AI generated summary from uploadedd documents will appear here"
              className="w-full border rounded-lg p-3 bg-gray-100 resize-none text-gray-700 cursor-allowed"
              />
        </div>

    </div>
);
}

export default Document;