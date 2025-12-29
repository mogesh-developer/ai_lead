import React from 'react';

const Guide = () => {
  const features = [
    {
      title: "Dashboard",
      description: "Your central command center for monitoring lead outreach performance.",
      why: "Provides a quick overview of your campaign's health and progress.",
      how: "Navigate to the Dashboard tab. View key metrics like Total Leads, Analyzed, Outreach Sent, and Converted. Toggle 'Autopilot Mode' to automate the entire process.",
      location: "Main Navigation > Dashboard"
    },
    {
      title: "Lead Discovery (Search)",
      description: "AI-powered tool to find new business leads from the web.",
      why: "Automates the tedious process of finding potential clients, their emails, and phone numbers.",
      how: "Go to 'Find Leads'. Enter an Industry (e.g., 'Software') and Location (e.g., 'New York'). Click 'Start Discovery'. The AI will scrape the web and populate your list.",
      location: "Main Navigation > Find Leads"
    },
    {
      title: "Lead Upload",
      description: "Import existing leads via CSV or manual entry.",
      why: "Allows you to bring in leads from other sources or add specific contacts you've met.",
      how: "Go to 'Upload Leads'. Choose 'CSV Upload' to drag-and-drop a file, or 'Manual Entry' to type in details one by one.",
      location: "Main Navigation > Upload Leads"
    },
    {
      title: "AI Analysis",
      description: "Intelligent scoring and categorization of leads.",
      why: "Helps prioritize high-value leads and filter out low-quality ones before spending time on outreach.",
      how: "On the Dashboard or Lead Detail page, click 'Analyze'. The AI evaluates the company's digital presence and assigns a Trust Score (0-100).",
      location: "Lead Detail Page > Analyze Button"
    },
    {
      title: "Automated Outreach",
      description: "AI-generated personalized emails sent automatically.",
      why: "Scales your outreach efforts while maintaining a personal touch, increasing response rates.",
      how: "After analysis, if a lead qualifies (High Trust Score), click 'Send Outreach' (or enable Autopilot). The AI drafts and sends the email.",
      location: "Lead Detail Page > Send Outreach"
    },
    {
      title: "Autopilot Mode",
      description: "Fully autonomous operation of the entire workflow.",
      why: "Runs your lead generation business in the background without manual intervention.",
      how: "Toggle the switch in the top-right corner of the Dashboard. The system will periodically find, analyze, and contact leads.",
      location: "Dashboard > Top Right Toggle"
    }
  ];

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-8 text-gray-800">User Guide & Features</h1>
      
      <div className="grid gap-8">
        {features.map((feature, index) => (
          <div key={index} className="bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-500">
            <h2 className="text-2xl font-semibold mb-3 text-gray-800">{feature.title}</h2>
            <p className="text-gray-600 mb-4 text-lg">{feature.description}</p>
            
            <div className="grid md:grid-cols-3 gap-4 mt-4 bg-gray-50 p-4 rounded-md">
              <div>
                <h3 className="font-bold text-blue-600 mb-1">Why use this?</h3>
                <p className="text-sm text-gray-700">{feature.why}</p>
              </div>
              <div>
                <h3 className="font-bold text-green-600 mb-1">How to use?</h3>
                <p className="text-sm text-gray-700">{feature.how}</p>
              </div>
              <div>
                <h3 className="font-bold text-purple-600 mb-1">Where is it?</h3>
                <p className="text-sm text-gray-700">{feature.location}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-12 bg-blue-50 p-8 rounded-lg border border-blue-100">
        <h2 className="text-2xl font-bold mb-4 text-blue-800">Need more help?</h2>
        <p className="text-blue-700">
          This AI Agent system is designed to be intuitive. If you encounter issues, check the console logs or ensure your API keys are correctly configured in the backend.
        </p>
      </div>
    </div>
  );
};

export default Guide;
