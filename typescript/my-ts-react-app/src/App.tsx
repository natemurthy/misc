import React from 'react';
import logo from './logo.svg';
import './App.css';
import { FC } from 'react'
import HelloWorld from './components/HelloWorld'
import List from './components/List'

function DefaultApp() {
  return (
    <div className="App">
      <header className="App-header">
        <img src={logo} className="App-logo" alt="logo" />
        <p>
          Edit <code>src/App.tsx</code> and save to reload.
        </p>
        <a
          className="App-link"
          href="https://reactjs.org"
          target="_blank"
          rel="noopener noreferrer"
        >
          Learn React
        </a>
      </header>
    </div>
  );
}

const avengers = [
  'Captain America',
  'Iron Man',
  'Black Widow',
  'Thor',
  'Hawkeye',
]

const App: FC = () => {
  return (
    <div className="App">
      <HelloWorld />
      <List data={avengers} />
    </div>
  );
}

export default App;
