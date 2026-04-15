import React, { useState } from "react";

function App() {
  const [destination, setDestination] = useState("");
  const [days, setDays] = useState(3);
  const [budget, setBudget] = useState("medium");
  const [interests, setInterests] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const interestOptions = ["culture", "history", "food", "nature", "nightlife", "shopping"];

  const toggleInterest = (interest) => {
    setInterests((prev) =>
      prev.includes(interest)
        ? prev.filter((item) => item !== interest)
        : [...prev, interest]
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
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
        throw new Error(data.detail || "Something went wrong");
      }

      setResult(data);
    } catch (err) {
      setError(err.message || "Failed to generate itinerary");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: "900px", margin: "0 auto", padding: "40px 20px", fontFamily: "Arial, sans-serif" }}>
      <h1>AI Smart Travel Planner</h1>
      <p>Plan a personalised trip using structured inputs and AI-generated itineraries.</p>

      <form onSubmit={handleSubmit} style={{ display: "grid", gap: "16px", marginTop: "24px" }}>
        <div>
          <label>Destination</label>
          <br />
          <input
            type="text"
            value={destination}
            onChange={(e) => setDestination(e.target.value)}
            placeholder="Enter a city"
            required
            style={{ width: "100%", padding: "10px", marginTop: "6px" }}
          />
        </div>

        <div>
          <label>Number of Days</label>
          <br />
          <input
            type="number"
            min="1"
            max="7"
            value={days}
            onChange={(e) => setDays(e.target.value)}
            required
            style={{ width: "100%", padding: "10px", marginTop: "6px" }}
          />
        </div>

        <div>
          <label>Budget</label>
          <br />
          <select
            value={budget}
            onChange={(e) => setBudget(e.target.value)}
            style={{ width: "100%", padding: "10px", marginTop: "6px" }}
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
        </div>

        <div>
          <label>Interests</label>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "10px", marginTop: "10px" }}>
            {interestOptions.map((interest) => (
              <button
                type="button"
                key={interest}
                onClick={() => toggleInterest(interest)}
                style={{
                  padding: "10px 14px",
                  border: "1px solid #ccc",
                  background: interests.includes(interest) ? "#ddd" : "#fff",
                  cursor: "pointer",
                }}
              >
                {interest}
              </button>
            ))}
          </div>
        </div>

        <button type="submit" style={{ padding: "12px", cursor: "pointer" }}>
          {loading ? "Generating..." : "Generate Itinerary"}
        </button>
      </form>

      {error && <p style={{ color: "red", marginTop: "20px" }}>{error}</p>}

      {result && result.itinerary && (
        <div style={{ marginTop: "40px" }}>
          <h2>{result.destination} Itinerary</h2>
          {result.itinerary.days.map((dayObj) => (
            <div key={dayObj.day} style={{ marginBottom: "24px", padding: "16px", border: "1px solid #ddd", borderRadius: "8px" }}>
              <h3>Day {dayObj.day}</h3>
              {dayObj.activities.map((activity, index) => (
                <div key={index} style={{ marginBottom: "12px" }}>
                  <strong>{activity.time}</strong> — {activity.place_name}
                  <br />
                  <span>{activity.activity}</span>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default App;