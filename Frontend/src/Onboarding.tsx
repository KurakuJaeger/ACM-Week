import { useState } from "react";

interface OnboardingProps {
  onComplete: () => void;
}

function Onboarding({ onComplete }: OnboardingProps) {
  const [currentStep, setCurrentStep] = useState(0);

  const features = [
    {
      title: "Real-Time Telemetry Dashboard",
      description: "Experience live F1 racing data as it happens. Monitor driver performance, car telemetry, and race conditions in real-time.",
      icon: "🏁",
      color: "from-red-500 to-red-600"
    },
    {
      title: "Driver Performance Metrics",
      description: "Track speed, RPM, throttle usage, gear shifts, and DRS activations for each driver. Visualize performance with interactive sparklines.",
      icon: "🚗",
      color: "from-blue-500 to-blue-600"
    },
    {
      title: "Session Information",
      description: "Get detailed info about the current race session, including event details, track temperature, and driver count.",
      icon: "📊",
      color: "from-green-500 to-green-600"
    },
    {
      title: "Top Lap Times",
      description: "View the fastest lap times and gaps to pole position. Stay updated with the current leaderboard standings.",
      icon: "⏱️",
      color: "from-purple-500 to-purple-600"
    },
    {
      title: "Live Connection Status",
      description: "Monitor your connection to the backend server and receive real-time updates on data availability.",
      icon: "📡",
      color: "from-orange-500 to-orange-600"
    }
  ];

  const nextStep = () => {
    if (currentStep < features.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      onComplete();
    }
  };

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const currentFeature = features[currentStep];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white flex items-center justify-center p-4" role="main" aria-label="F1 Pitwall AI Onboarding">
      {/* F1 Checkered Background Pattern */}
      <div className="absolute inset-0 opacity-5 overflow-hidden" aria-hidden="true">
        <svg width="100%" height="100%" className="absolute inset-0">
          <defs>
            <pattern id="checkered" x="0" y="0" width="40" height="40" patternUnits="userSpaceOnUse">
              <rect x="0" y="0" width="20" height="20" fill="white"/>
              <rect x="20" y="0" width="20" height="20" fill="black"/>
              <rect x="0" y="20" width="20" height="20" fill="black"/>
              <rect x="20" y="20" width="20" height="20" fill="white"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#checkered)"/>
        </svg>
      </div>

      <div className="relative z-10 max-w-4xl w-full">
        {/* Header */}
        <header className="text-center mb-12">
          <div className="flex items-center justify-center mb-6">
            <div className="w-16 h-16 bg-gradient-to-r from-red-500 to-red-600 rounded-full flex items-center justify-center text-3xl mr-4" aria-hidden="true">
              🏎️
            </div>
            <h1 className="text-5xl font-bold bg-gradient-to-r from-red-400 via-white to-red-400 bg-clip-text text-transparent">
              F1-PITWALL-AI
            </h1>
          </div>
          <p className="text-xl text-slate-300 mb-8">
            Your Ultimate F1 Telemetry Companion
          </p>
          <div className="flex items-center justify-center space-x-2" role="tablist" aria-label="Onboarding steps">
            {features.map((_, index) => (
              <button
                key={index}
                onClick={() => setCurrentStep(index)}
                className={`w-3 h-3 rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-red-500 ${
                  index === currentStep ? 'bg-red-500' : 'bg-slate-600'
                }`}
                aria-label={`Go to step ${index + 1}: ${features[index].title}`}
                aria-selected={index === currentStep}
                role="tab"
              />
            ))}
          </div>
        </header>

        {/* Feature Card */}
        <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-8 border border-slate-700 shadow-2xl mb-8">
          <div className="text-center mb-8">
            <div className={`w-20 h-20 bg-gradient-to-r ${currentFeature.color} rounded-full flex items-center justify-center text-4xl mx-auto mb-6 shadow-lg`}>
              {currentFeature.icon}
            </div>
            <h2 className="text-3xl font-bold mb-4 text-white">
              {currentFeature.title}
            </h2>
            <p className="text-lg text-slate-300 leading-relaxed max-w-2xl mx-auto">
              {currentFeature.description}
            </p>
          </div>

          {/* Feature Preview (simplified) */}
          <div className="bg-slate-900/50 rounded-lg p-6 border border-slate-600">
            <div className="text-center text-slate-400">
              <p className="mb-4">Preview of {currentFeature.title}</p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                {currentStep === 0 && (
                  <>
                    <div className="bg-green-500/20 text-green-400 px-3 py-2 rounded">
                      ● Live Connection
                    </div>
                    <div className="bg-slate-700 px-3 py-2 rounded">
                      Real-time Updates
                    </div>
                    <div className="bg-slate-700 px-3 py-2 rounded">
                      WebSocket Stream
                    </div>
                    <div className="bg-slate-700 px-3 py-2 rounded">
                      Live Dashboard
                    </div>
                  </>
                )}
                {currentStep === 1 && (
                  <>
                    <div className="bg-blue-500/20 text-blue-400 px-3 py-2 rounded">
                      Speed: 320 km/h
                    </div>
                    <div className="bg-yellow-500/20 text-yellow-400 px-3 py-2 rounded">
                      Throttle: 95%
                    </div>
                    <div className="bg-purple-500/20 text-purple-400 px-3 py-2 rounded">
                      RPM: 12,000
                    </div>
                    <div className="bg-green-500/20 text-green-400 px-3 py-2 rounded">
                      DRS: Active
                    </div>
                  </>
                )}
                {currentStep === 2 && (
                  <>
                    <div className="bg-slate-700 px-3 py-2 rounded">
                      Event: Monaco GP
                    </div>
                    <div className="bg-slate-700 px-3 py-2 rounded">
                      Session: Race
                    </div>
                    <div className="bg-slate-700 px-3 py-2 rounded">
                      Drivers: 20
                    </div>
                    <div className="bg-slate-700 px-3 py-2 rounded">
                      Track: 45°C
                    </div>
                  </>
                )}
                {currentStep === 3 && (
                  <>
                    <div className="bg-red-500/20 text-red-400 px-3 py-2 rounded">
                      P1: 1:12.345
                    </div>
                    <div className="bg-slate-700 px-3 py-2 rounded">
                      Gap: +0.567s
                    </div>
                    <div className="bg-slate-700 px-3 py-2 rounded">
                      Driver: Verstappen
                    </div>
                    <div className="bg-slate-700 px-3 py-2 rounded">
                      Team: Red Bull
                    </div>
                  </>
                )}
                {currentStep === 4 && (
                  <>
                    <div className="bg-green-500/20 text-green-400 px-3 py-2 rounded">
                      Status: Connected
                    </div>
                    <div className="bg-slate-700 px-3 py-2 rounded">
                      Backend: Online
                    </div>
                    <div className="bg-slate-700 px-3 py-2 rounded">
                      Updates: Live
                    </div>
                    <div className="bg-slate-700 px-3 py-2 rounded">
                      Data: Streaming
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex justify-between items-center" aria-label="Onboarding navigation">
          <button
            onClick={prevStep}
            disabled={currentStep === 0}
            className="px-6 py-3 bg-slate-700 hover:bg-slate-600 disabled:bg-slate-800 disabled:cursor-not-allowed rounded-lg font-semibold transition-colors border border-slate-600 focus:outline-none focus:ring-2 focus:ring-red-500"
            aria-label="Previous feature"
          >
            Previous
          </button>

          <div className="text-slate-400" aria-live="polite">
            {currentStep + 1} of {features.length}
          </div>

          <button
            onClick={nextStep}
            className="px-6 py-3 bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 rounded-lg font-semibold transition-colors shadow-lg focus:outline-none focus:ring-2 focus:ring-red-500"
            aria-label={currentStep === features.length - 1 ? 'Complete onboarding and start using the app' : 'Next feature'}
          >
            {currentStep === features.length - 1 ? 'Get Started' : 'Next'}
          </button>
        </nav>

        {/* Skip Option */}
        <div className="text-center mt-6">
          <button
            onClick={onComplete}
            className="text-slate-400 hover:text-white transition-colors text-sm underline focus:outline-none focus:ring-2 focus:ring-red-500 rounded px-2 py-1"
            aria-label="Skip onboarding and go directly to the app"
          >
            Skip onboarding
          </button>
        </div>
      </div>
    </div>
  );
}

export default Onboarding;