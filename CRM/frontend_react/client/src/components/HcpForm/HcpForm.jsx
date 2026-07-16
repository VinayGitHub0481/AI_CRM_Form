import InteractionDetails from "./Interaction";
import MaterialsSection from "./MaterialBox";
import SentimentSection from "./HcpSentiment";
import OutcomeBox from "./OutcomeBox";
import FollowUpBox from "./FollowUpBox";
import Document from "./Document";

function HCPForm({

    formData,
    outcome,
    followUp,
    summary

}) {

    return (

        <div className="space-y-5">

            {/* Interaction Details */}
            <InteractionDetails
                formData={formData}
            />

           {/* Materials Shared */}
            <MaterialsSection
                formData={formData}
            />

           {/* AI Detected Sentiment */}
            <SentimentSection
                formData={formData}
            />

           {/*AI Generated Outcome */}
            <OutcomeBox outcome={outcome} />

            {/*AI PDF summary */}
            <Document summary={summary} />

            {/* AI suggested Follow-up */}
            <FollowUpBox followUp={followUp} />

        </div>

    );

}

export default HCPForm;