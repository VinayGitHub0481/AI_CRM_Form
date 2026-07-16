



function OutcomeBox({ outcome }) {
  return (
    <div className="bg-white shadow rounded-lg p-6">

      <h2 className="text-xl font-bold text-gray-800 border-b pb-2 mb-4">
        Outcome
      </h2>

      <textarea
        rows={8}
        value={outcome || ""}  //here if response is outcome then will be dispalyed or else ""
        readOnly           
        placeholder="conversation..."
        className="w-full border rounded-lg p-4 bg-white-100 text-gray-700 resize-none cursor-allowed focus:outline-none"
      />

    </div>
  );
}

export default OutcomeBox;


































// function OutcomeBox({ outcome }) {

//     return (

//         <div className="bg-white shadow rounded-lg p-4">

//             <h2 className="font-bold mb-3">

//                 AI Outcomes

//             </h2>

//             <textarea

//                 rows={6}

//                 value={outcome}

//                 readOnly

//                 placeholder="AI generated outcome will appear here..."

//                 className="border w-full p-2 rounded bg-gray-50"

//             />

//         </div>

//     );

// }

// export default OutcomeBox;