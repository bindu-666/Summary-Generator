import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Signup from './pages/Signup';
import Upload from './pages/Upload';
import Quiz from './pages/Quiz';
import History from './pages/History';
import Settings from './pages/Settings';
import Home from './pages/Home';
import PrivateRoute from './components/PrivateRoute';
import QuizList from './pages/QuizList';
import SummaryGenerator from './pages/SummaryGenerator';
import FileViewer from './pages/FileViewer';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/" element={<PrivateRoute><Home /></PrivateRoute>} />
        <Route path="/upload" element={<PrivateRoute><Upload /></PrivateRoute>} />
        <Route path="/quiz" element={<PrivateRoute><QuizList /></PrivateRoute>} />
        <Route path="/quiz/:filename" element={<PrivateRoute><Quiz /></PrivateRoute>} />                                                                                  
        <Route path="/history" element={<PrivateRoute><History /></PrivateRoute>} />
        <Route path="/settings" element={<PrivateRoute><Settings /></PrivateRoute>} />
        <Route path="/summary-generator" element={<PrivateRoute><SummaryGenerator /></PrivateRoute>} />
        <Route path="/file/:filename" element={<PrivateRoute><FileViewer /></PrivateRoute>} />
      </Routes>
    </Router>
  );
}

export default App; 