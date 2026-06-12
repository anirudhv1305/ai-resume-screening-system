function getStatus(score) {
  if (score >= 75) return "Good";
  if (score >= 50) return "Average";
  return "Weak";
}

export default function CandidateTable({
  rankings,
  loading,
  activeJob,
  skillFilter,
  setSkillFilter,
  onApplyFilter,
  onResetFilter,
  selectedCandidateId,
  onSelectCandidate,
  averageScore,
  topScore,
  candidateCount,
}) {
  return (
    <section className="candidate-panel">
      <div className="list-toolbar">
        <div>
          <p className="surface-label">Candidates</p>
          <h1>{activeJob ? activeJob.title : "No active job selected"}</h1>
          <div className="job-context">
            <span>{candidateCount} resumes</span>
            <span>{rankings.length} ranked</span>
            <span>{activeJob?.minimum_years_experience || 0} yrs required</span>
          </div>
        </div>

        <form
          className="skill-filter"
          onSubmit={(event) => {
            event.preventDefault();
            onApplyFilter();
          }}
        >
          <input
            type="text"
            value={skillFilter}
            placeholder="Filter by skill"
            onChange={(event) => setSkillFilter(event.target.value)}
          />
          <button className="small-button" type="submit">
            Apply
          </button>
          <button className="small-button ghost" type="button" onClick={onResetFilter}>
            Reset
          </button>
        </form>
      </div>

      <div className="score-summary" aria-label="Score summary">
        <div>
          <span>Average match</span>
          <strong>{averageScore === null ? "--" : averageScore.toFixed(1)}</strong>
        </div>
        <div>
          <span>Top candidate</span>
          <strong>{topScore === null ? "--" : topScore.toFixed(1)}</strong>
        </div>
        <div>
          <span>Required skills</span>
          <strong>{activeJob?.required_skills?.length || 0}</strong>
        </div>
      </div>

      <div className="table-scroll">
        <table className="candidate-table">
          <thead>
            <tr>
              <th>Name / File Name</th>
              <th>Score</th>
              <th>Experience</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td className="table-state" colSpan="4">
                  <span className="loading-pulse" />
                  Analyzing candidates...
                </td>
              </tr>
            ) : rankings.length ? (
              rankings.map((candidate) => {
                const status = getStatus(candidate.match_score);
                const selected = candidate.candidate_id === selectedCandidateId;
                return (
                  <tr
                    key={candidate.candidate_id}
                    className={selected ? "selected-row" : ""}
                    onClick={() => onSelectCandidate(candidate.candidate_id)}
                    tabIndex="0"
                    onKeyDown={(event) => {
                      if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        onSelectCandidate(candidate.candidate_id);
                      }
                    }}
                  >
                    <td>
                      <div className="candidate-name">
                        <strong>{candidate.candidate_name || candidate.filename}</strong>
                        <span>{candidate.email || candidate.filename}</span>
                      </div>
                    </td>
                    <td className="score-cell">{candidate.match_score.toFixed(1)}</td>
                    <td>{candidate.experience_years.toFixed(1)} yrs</td>
                    <td>
                      <span className={`status-pill status-${status.toLowerCase()}`}>
                        {status}
                      </span>
                    </td>
                  </tr>
                );
              })
            ) : (
              <tr>
                <td className="table-state" colSpan="4">
                  No ranked candidates yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
