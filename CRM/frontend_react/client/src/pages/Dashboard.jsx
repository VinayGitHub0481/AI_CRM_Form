

import { useState,useEffect } from "react";

import HCPForm from "../components/HcpForm/HCPForm";
import Chatbot from "../components/ChatBot/Chatbot";
import { Summary } from "lucide-react";


function Dashboard() {

  const [formData, setFormData] = useState({
    hcpName: "",
    interactionType: "",
    date: "",
    time: "",
    attendees: [],
    topicsDiscussed: [],
    materialsShared: [],
    sentiment: "",
    summary:""
  });

  const [outcome, setOutcome] = useState("");

  const [followUp, setFollowUp] = useState({
    required: false,
    date: "",
    purpose: ""
  });

  const [summary,setSummary]=useState("");

  //trying to debug what is actual response 
  useEffect(()=>{
    console.log("Dashboard form :",formData);
  }, [formData]);

 useEffect(()=>{
    console.log("Dashboard outcome :",outcome);
  }, [outcome]);

 useEffect(()=>{
    console.log("Dashboard followUp :",followUp);
  }, [followUp]);

useEffect(() => {
  console.log("Dashboard summary:", summary);
}, [summary]);


  /**
   * Called ONLY by Chatbot after LangGraph response
   */
  const updateFromAI = (response) => {

    if (response.form) {
      setFormData(prev => ({
        ...prev,
        ...response.form   //this is the ai response 

      }));
    }

    if ("outcome" in response) {
      setOutcome(response.outcome);
    }

    if (response.followUp) {
      setFollowUp(prev=>({
        ...prev,
        ...response.followUp
      }));
    }

    if ("summary" in response){
      setSummary(response.summary);
    }

  };
  

  

  return (

    <div className="h-[calc(100vh-64px)] flex overflow-hidden">

      {/* Left Side */}
      <div className="w-1/2 bg-white overflow-y-auto p-5">

        <HCPForm
          formData={formData}
          outcome={outcome}
          followUp={followUp}
          summary={summary}
        />

      </div>

      {/* Right Side */}

      <div className="w-1/2 bg-gray-100 overflow-y-auto p-5">

        <Chatbot
          updateFromAI={updateFromAI}
        />

      </div>

    </div>

  );
}

export default Dashboard;



















































// function Dashboard() {

// const [formData,setFormData] = useState({
//     hcpName:"",
//     interactionType:"",
//     date:"",
//     time:"",
//     attendees:"",
//     topicsDiscussed:"",
//     materialsShared:[],
//     sentiment:""
// });


// const [outcome,setOutcome]=useState("");

// const [followUp,setFollowUp]=useState("");


// return (

// <div className="h-[calc(100vh-64px)] flex overflow-hidden">


// <div className="w-1/2 overflow-y-auto p-4 bg-white">

// <HCPForm
//     formData={formData}
//     outcome={outcome}
//     followUp={followUp}
// />

// </div>


// <div className="w-1/2 overflow-y-auto p-4 bg-gray-50">

// <Chatbot
//     setFormData={setFormData}
//     setOutcome={setOutcome}
//     setFollowUp={setFollowUp}
// />

// </div>


// </div>

// )

// }

// export default Dashboard;

