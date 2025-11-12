import React, { useState, useEffect } from 'react';
import './App.css';
import QuestionList from './components/QuestionList';
import ContractList from './components/ContractList';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div>
          <h1>Something went wrong.</h1>
          <pre>{this.state.error.toString()}</pre>
        </div>
      );
    }

    return this.props.children;
  }
}

function App() {
  const [questions, setQuestions] = useState([]);
  const [contracts, setContracts] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const questionsResponse = await fetch('http://localhost:8000/questions');
        if (!questionsResponse.ok) {
          throw new Error(`HTTP error! status: ${questionsResponse.status}`);
        }
        const questionsData = await questionsResponse.json();
        setQuestions(questionsData);

        const contractsResponse = await fetch('http://localhost:8000/contracts');
        if (!contractsResponse.ok) {
          throw new Error(`HTTP error! status: ${contractsResponse.status}`);
        }
        const contractsData = await contractsResponse.json();
        setContracts(contractsData);
      } catch (e) {
        setError(e.toString());
        console.error('Error fetching data:', e);
      }
    }

    fetchData();
  }, []);

  return (
    <ErrorBoundary>
      <div className="app">
        <header className="header">
          <h1>Prediction Market Screener</h1>
        </header>
        <div className="container">
          <aside className="sidebar">
            <h2>Controls</h2>
            {/* Future controls will go here */}
          </aside>
          <main className="main-content">
            {error ? (
              <div>
                <h2>Error</h2>
                <p>{error}</p>
              </div>
            ) : (
              <>
                <QuestionList questions={questions} />
                <ContractList contracts={contracts} />
              </>
            )}
          </main>
        </div>
      </div>
    </ErrorBoundary>
  );
}

export default App;
