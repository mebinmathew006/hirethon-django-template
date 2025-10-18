import React ,{ StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import { PersistGate } from 'redux-persist/lib/integration/react.js'
import { Provider } from 'react-redux'
import store, { persistor } from './store/store.js'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <Provider store={store}>
    <PersistGate loading={null} persistor={persistor}>
      <App />
  </PersistGate >
  </Provider>

)
