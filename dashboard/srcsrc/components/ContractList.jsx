import React from 'react';

function ContractList({ contracts }) {
  return (
    <div>
      <h2>Contracts</h2>
      {contracts.map((contract) => (
        <div key={contract.id}>
          <h3>{contract.id}</h3>
          <p>Platform: {contract.platform}</p>
        </div>
      ))}
    </div>
  );
}

export default ContractList;
