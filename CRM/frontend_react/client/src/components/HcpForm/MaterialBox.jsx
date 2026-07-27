


function MaterialsSection({ formData }) {

  //using this approach to prevent from errors if backend sends string instead of array form 
  const materials=Array.isArray(formData.materialsShared)
             ? formData.materialsShared: [];

  return (
    <div className="bg-white shadow rounded-lg p-6">

      <h2 className="text-xl font-bold text-gray-800 border-b pb-2 mb-4">
        Materials Shared
      </h2>

      {materials.length === 0 ? (

        <div className="flex items-center justify-center h-24 rounded-lg border-2 border-dashed border-gray-300 bg-gray-50">

          <p className="text-gray-500 italic">
            AI will extract shared materials from the conversation.
          </p>

        </div>

      ) : (

        <div className="flex flex-wrap gap-3">

          {materials.map((material, index) => (
            <div
              key={index}
              className="px-4 py-2 rounded-full bg-blue-100 text-blue-800 border border-blue-200 text-sm font-medium"
            >
              {material}
            </div>
          ))}

        </div>

      )}

    </div>
  );
}

export default MaterialsSection;











































































