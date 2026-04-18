import React, { useMemo, useState } from "react";
import "./App.css";

const INTEREST_OPTIONS = [
  "culture",
  "history",
  "food",
  "nature",
  "nightlife",
  "shopping",
];

function App() {
  const [step, setStep] = useState(1);
  const [destination, setDestination] = useState("");
  const [days, setDays] = useState(3);
  const [budget, setBudget] = useState("medium");
  const [interests, setInterests] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const pageTitle = useMemo(() => {
    if (step === 1) return "Welcome";
    if (step === 2) return "Trip Details";
    if (step === 3) return "Preferences";
    if (step === 4) return "Review";
    if (step === 5) return "Your Itinerary";
    return "AI Smart Travel Planner";
  }, [step]);

  const toggleInterest = (interest) => {
    setInterests((prev) =>
      prev.includes(interest)
        ? prev.filter((item) => item !== interest)
        : [...prev, interest]
    );
  };

  const goNext = () => {
    if (step === 2) {
      if (!destination.trim()) {
        setError("Please enter a destination.");
        return;
      }
      if (!days || parseInt(days, 10) < 1) {
        setError("Please enter a valid number of days.");
        return;
      }
    }

    if (step === 3 && interests.length === 0) {
      setError("Please select at least one interest.");
      return;
    }

    setError("");
    setStep((prev) => prev + 1);
  };

  const goBack = () => {
    setError("");
    setStep((prev) => prev - 1);
  };

  const handleGenerate = async () => {
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch("http://127.0.0.1:8000/generate-itinerary", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          destination,
          interests,
          budget,
          days: parseInt(days, 10),
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || data.error || "Something went wrong.");
      }

      if (!data.itinerary) {
        throw new Error("No itinerary was returned.");
      }

      setResult(data.itinerary);
      setStep(5);
    } catch (err) {
      setError(err.message || "Failed to generate itinerary.");
    } finally {
      setLoading(false);
    }
  };

  const resetPlanner = () => {
    setStep(1);
    setDestination("");
    setDays(3);
    setBudget("medium");
    setInterests([]);
    setResult(null);
    setError("");
    setLoading(false);
  };

  const renderProgress = () => (
    <div className="progress-wrap">
      {[1, 2, 3, 4, 5].map((item) => (
        <div
          key={item}
          className={`progress-step ${step === item ? "active" : ""}`}
        >
          Step {item}
        </div>
      ))}
    </div>
  );

  const renderWelcome = () => (
    <>
      <h2 className="section-title">Plan your next trip with AI</h2>
      <div className="button-row">
        <div />
        <button className="primary-btn" onClick={goNext}>
          Start Planning
        </button>
      </div>
    </>
  );

  const renderDetails = () => (
    <>
      <h2 className="section-title">Enter your trip details</h2>

      <label className="label">Destination</label>
      <input
        className="input"
        type="text"
        value={destination}
        onChange={(e) => setDestination(e.target.value)}
        placeholder="Enter a city, e.g. Paris"
      />

      <label className="label">Number of Days</label>
      <input
        className="input"
        type="number"
        min="1"
        max="7"
        value={days}
        onChange={(e) => setDays(e.target.value)}
      />

      <label className="label">Budget</label>
      <select
        className="input"
        value={budget}
        onChange={(e) => setBudget(e.target.value)}
      >
        <option value="low">Low</option>
        <option value="medium">Medium</option>
        <option value="high">High</option>
      </select>

      <div className="button-row">
        <button className="secondary-btn" onClick={goBack}>
          Back
        </button>
        <button className="primary-btn" onClick={goNext}>
          Next
        </button>
      </div>
    </>
  );

  const renderPreferences = () => (
    <>
      <h2 className="section-title">Choose your interests</h2>
      <p className="subtext">
        Your selections help the system retrieve relevant place types and shape
        the itinerary more accurately.
      </p>

      <div className="chip-wrap">
        {INTEREST_OPTIONS.map((interest) => (
          <button
            key={interest}
            type="button"
            className={`chip ${interests.includes(interest) ? "selected" : ""}`}
            onClick={() => toggleInterest(interest)}
          >
            {interest}
          </button>
        ))}
      </div>

      <div className="button-row">
        <button className="secondary-btn" onClick={goBack}>
          Back
        </button>
        <button className="primary-btn" onClick={goNext}>
          Next
        </button>
      </div>
    </>
  );

  const renderReview = () => (
    <>
      <h2 className="section-title">Review your trip plan</h2>

      <div className="summary-card">
        <strong>Destination:</strong> {destination}
        <br />
        <strong>Days:</strong> {days}
        <br />
        <strong>Budget:</strong> {budget}
        <br />
        <strong>Interests:</strong> {interests.join(", ")}
      </div>

      <div className="button-row">
        <button className="secondary-btn" onClick={goBack}>
          Back
        </button>
        <button className="primary-btn" onClick={handleGenerate}>
          {loading ? "Generating..." : "Generate Itinerary"}
        </button>
      </div>
    </>
  );

  const renderItinerary = () => {
    if (!result) return null;

    return (
      <>
        <h2 className="section-title">{result.destination} Itinerary</h2>

        {result.days.map((dayObj) => (
          <div key={dayObj.day_number} className="day-card">
            <h3>Day {dayObj.day_number}</h3>

            {dayObj.activities.map((activity, index) => (
              <div
                key={`${dayObj.day_number}-${index}`}
                className={`activity-row ${
                  index === dayObj.activities.length - 1 ? "no-border" : ""
                }`}
              >
                <strong>{activity.time}</strong> — {activity.name}

                <div className="activity-meta">
                  <div>
                    <strong>Category:</strong> {activity.category}
                  </div>
                  <div>
                    <strong>Reason:</strong> {activity.rationale}
                  </div>
                  <div className="map-link-wrap">
                    <a
                      href={`https://www.google.com/maps/search/?api=1&query=Google&query_place_id=${activity.place_id}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="map-link"
                    >
                      View on Google Maps
                    </a>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ))}

        {result.notes && (
          <div className="notes-box">
            <strong>Notes:</strong> {result.notes}
          </div>
        )}

        <div className="button-row">
          <button className="secondary-btn" onClick={resetPlanner}>
            Plan Another Trip
          </button>
        </div>
      </>
    );
  };

  const renderStepContent = () => {
    if (step === 1) return renderWelcome();
    if (step === 2) return renderDetails();
    if (step === 3) return renderPreferences();
    if (step === 4) return renderReview();
    if (step === 5) return renderItinerary();
    return null;
  };

  return (
    <div className="app">
      <div className="container">
        <h1 className="heading">AI Smart Travel Planner</h1>
        <p className="subtext">{pageTitle}</p>

        {renderProgress()}
        {renderStepContent()}

        {error && <div className="error-box">{error}</div>}
        {loading && step !== 4 && (
          <div className="loading-text">Generating your itinerary...</div>
        )}
      </div>
    </div>
  );
}

export default App;