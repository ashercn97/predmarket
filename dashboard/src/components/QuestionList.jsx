import React from 'react';

function QuestionList({ questions }) {
  return (
    <div>
      <h2>Questions</h2>
      {questions.map((question) => (
        <div key={question.id}>
          <h3>{question.title}</h3>
          <p>Platform: {question.platform}</p>
        </div>
      ))}
    </div>
  );
}

export default QuestionList;
