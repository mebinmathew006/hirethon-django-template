import React, { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import { BrowserRouter } from 'react-router-dom'
import { ToastContainer } from "react-toastify";
import AppRoutes from './router/AppRoutes'
function App() {
  const [count, setCount] = useState(0)

  return (
    <BrowserRouter>
            <ToastContainer />
            <AppRoutes />
          </BrowserRouter>
  )
}

export default App
