import { BrowserRouter, Routes, Route } from 'react-router-dom';
import FirstRunGate from './FirstRunGate';
import Welcome from './routes/Welcome';
import Library from './routes/Library';
import NewReading from './routes/NewReading';
import NewReadingPaste from './routes/NewReadingPaste';
import NewReadingPdf from './routes/NewReadingPdf';
import NewReadingUrl from './routes/NewReadingUrl';
import Reader from './routes/Reader';
import Settings from './routes/Settings';
import Completion from './routes/Completion';
import Share from './routes/Share';

export default function App() {
  return (
    <BrowserRouter>
      <FirstRunGate>
        <Routes>
          <Route path="/" element={<Welcome />} />
          <Route path="/library" element={<Library />} />
          <Route path="/new" element={<NewReading />} />
          <Route path="/new/paste" element={<NewReadingPaste />} />
          <Route path="/new/pdf" element={<NewReadingPdf />} />
          <Route path="/new/url" element={<NewReadingUrl />} />
          <Route path="/reader" element={<Reader />} />
          <Route path="/reader/:id" element={<Reader />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/completion/:id" element={<Completion />} />
          <Route path="/share" element={<Share />} />
        </Routes>
      </FirstRunGate>
    </BrowserRouter>
  );
}
