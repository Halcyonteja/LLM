/**
 * TeachingPanel — shows current assistant text and list of example concepts to start.
 */
export default function TeachingPanel({
  assistantText,
  concepts,
  onStartConcept,
  disabled,
}) {
  return (
    <>
      <div className="panel">
        <h3>Tutor</h3>
        <p>{assistantText || "Choose a topic or type a question. Say \"Explain X\" to start."}</p>
      </div>
      {concepts && concepts.length > 0 && (
        <div className="panel">
          <h3>Try a concept</h3>
          <ul className="concept-list">
            {concepts.map((c, i) => (
              <li key={i}>
                <button
                  type="button"
                  className="btn"
                  disabled={disabled}
                  onClick={() => onStartConcept(c)}
                >
                  {c}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </>
  );
}
