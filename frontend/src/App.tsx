import React, { useState } from 'react';
import { Stack } from '@fluentui/react';
import { initializeIcons } from '@fluentui/react/lib/Icons';
import DOMPurify from 'dompurify';

// Initialize FluentUI icons
initializeIcons();

// Types
interface DocumentComparisonChange {
  description: string;
  search_string: string;
  context: string;
}

interface DocumentComparisonResult {
  diff_text: string;
  similarity_score: number;
  changelog: {
    summary: string;
    changes: DocumentComparisonChange[];
  };
  warning: boolean;
}

type Tab = 'summary' | 'differences';

interface ComparisonStep {
  mode: 'upload' | 'demo' | null;
  stage: 'select' | 'ready' | 'comparing' | 'complete';
}

// Add Citation interface
interface Citation {
  lineNumber: number;
  text: string;
}

// Styles
const styles = {
  container: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    marginTop: '1rem',
  } as const,
  chatContainer: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    width: '100%',
    maxHeight: 'calc(100vh - 10rem)',
  } as const,
  title: {
    fontSize: '2.75rem',
    fontWeight: 600,
    marginTop: 0,
    marginBottom: '1.875rem',
    '@media (min-width: 992px)': {
      fontSize: '4rem',
    },
  },
  subtitle: {
    fontWeight: 600,
    marginBottom: '0.625rem',
  },
  messageStream: {
    flexGrow: 1,
    maxHeight: '64rem',
    width: '100%',
    overflowY: 'auto',
    padding: '0 2rem',
    display: 'flex',
    flexDirection: 'column',
    resize: 'horizontal',
    minWidth: '50vw',
  } as const,
  inputSection: {
    position: 'sticky',
    bottom: 0,
    flex: '0 0 6.25rem',
    padding: '1rem',
    width: '100%',
    maxWidth: '64.25rem',
    background: '#f2f2f2',
    '@media (min-width: 992px)': {
      padding: '0.75rem 1.5rem 1.5rem',
    },
  } as const,
  fileInputs: {
    display: 'flex',
    gap: '1rem',
    marginBottom: '1rem',
  },
  button: {
    backgroundColor: '#222222',
    color: '#f2f2f2',
    padding: '0.75rem 1.5rem',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontWeight: 600,
    transition: 'opacity 0.2s',
    '&:hover': {
      opacity: 0.9,
    },
    '&:disabled': {
      opacity: 0.5,
      cursor: 'not-allowed',
    },
  },
  diffViewer: {
    padding: '2rem',
    background: '#fff',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    margin: '1rem 0',
    maxWidth: '100%',
  },
  header: {
    backgroundColor: '#222222',
    color: '#f2f2f2',
    padding: '1rem',
    width: '100%',
  },
  headerContent: {
    maxWidth: '64.25rem',
    margin: '0 auto',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
};

// Components
const Header = () => (
  <header style={styles.header}>
    <div style={styles.headerContent}>
      <h1 style={{ margin: 0, fontSize: '1.5rem' }}>Document Comparison - Solution Accelerator</h1>
    </div>
  </header>
);

const Button: React.FC<{
  onClick: () => void;
  disabled?: boolean;
  loading?: boolean;
  children: React.ReactNode;
}> = ({ onClick, disabled, loading, children }) => (
  <button
    onClick={onClick}
    disabled={disabled || loading}
    className="custom-button"
  >
    {loading ? <div className="loading-spinner" /> : children}
  </button>
);

const TabSelector: React.FC<{
  activeTab: Tab;
  onTabChange: (tab: Tab) => void;
}> = ({ activeTab, onTabChange }) => (
  <div className="tabs">
    <button
      className={`tab ${activeTab === 'summary' ? 'active' : ''}`}
      onClick={() => onTabChange('summary')}
    >
      Summary & Changes
    </button>
    <button
      className={`tab ${activeTab === 'differences' ? 'active' : ''}`}
      onClick={() => onTabChange('differences')}
    >
      Document Differences
    </button>
  </div>
);

// Add these utility functions at the top level
const ITEM_HEIGHT = 24; // Height of each diff line in pixels
const BUFFER_SIZE = 50; // Number of items to render above/below visible area

// Utility function to find citation
const findCitation = (searchString: string, diffText: string): number | null => {
  console.log('searchString:', searchString);
  if (!searchString || !diffText) return null;
  
  const cleanSearchString = searchString
    .trim()
    .replace(/[-[\]{}()*+?.,\\^$|#\s]/g, '\\$&');
  
  try {
    // Look for any matching line in the diff text
    const regex = new RegExp(`^[+-]?.*${cleanSearchString}.*$`, 'gm');
    const match = regex.exec(diffText);
    
    if (match) {
      // Count newlines up to the first match to get line number
      return diffText.slice(0, match.index).split('\n').length;
    }
  } catch (e) {
    console.error('Citation search error:', e);
  }
  
  return null;
};

// Update DiffViewer component
const DiffViewer: React.FC<{
  diffText: string;
  similarityScore: number;
  warning: boolean;
  scrollToLine?: number;
}> = ({ diffText, similarityScore, warning, scrollToLine }) => {
  const lines = diffText.split('\n');
  const containerRef = React.useRef<HTMLDivElement>(null);
  const [scrollTop, setScrollTop] = React.useState(0);
  const [viewportHeight, setViewportHeight] = React.useState(0);

  React.useEffect(() => {
    const updateViewport = () => {
      if (containerRef.current) {
        setViewportHeight(containerRef.current.clientHeight);
      }
    };

    updateViewport();
    window.addEventListener('resize', updateViewport);

    // Create IntersectionObserver to detect when container is visible
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          updateViewport();
        }
      },
      { threshold: 0.1 }
    );

    if (containerRef.current) {
      observer.observe(containerRef.current);
    }

    return () => {
      window.removeEventListener('resize', updateViewport);
      observer.disconnect();
    };
  }, []);

  const handleScroll = React.useCallback((e: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(e.currentTarget.scrollTop);
  }, []);

  // Calculate visible range with larger buffer
  const visibleStartIndex = Math.max(0, Math.floor(scrollTop / ITEM_HEIGHT) - BUFFER_SIZE);
  const visibleEndIndex = Math.min(
    lines.length,
    Math.ceil((scrollTop + viewportHeight) / ITEM_HEIGHT) + BUFFER_SIZE
  );
  
  const visibleLines = lines.slice(visibleStartIndex, visibleEndIndex);
  const totalHeight = lines.length * ITEM_HEIGHT;

  React.useEffect(() => {
    if (scrollToLine && containerRef.current) {
      const targetScrollTop = (scrollToLine - 1) * ITEM_HEIGHT;
      containerRef.current.scrollTo({
        top: targetScrollTop - (viewportHeight / 2),
        behavior: 'smooth'
      });
    }
  }, [scrollToLine, viewportHeight]);

  return (
    <div className="diff-viewer">
      <div className="diff-header">
        <span/>
        <span className={warning ? 'similarity-warning' : 'similarity-score'}>
          Similarity Score: {(similarityScore * 100).toFixed(2)}%
        </span>
      </div>
      
      <div 
        ref={containerRef}
        className="diff-content"
        onScroll={handleScroll}
      >
        <div 
          style={{ 
            height: `${totalHeight}px`, 
            position: 'relative',
            minHeight: '100%',
          }}
        >
          {visibleLines.map((line, i) => {
            const absoluteIndex = visibleStartIndex + i;
            return (
              <div 
                key={absoluteIndex}
                className={`diff-line ${line.startsWith('+') ? 'addition' : line.startsWith('-') ? 'deletion' : ''}`}
                style={{
                  transform: `translateY(${absoluteIndex * ITEM_HEIGHT}px)`,
                  position: 'absolute',
                  left: 0,
                  right: 0,
                  height: `${ITEM_HEIGHT}px`,
                }}
              >
                <span className="line-number">{absoluteIndex + 1}</span>
                <span className="line-text">{line}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

// Update ChangelogViewer to use list items
const ChangelogViewer: React.FC<{
  summary: string;
  changes: DocumentComparisonChange[];
  diffText: string;
  onCitationClick?: (lineNumber: number) => void;
}> = ({ summary, changes, diffText, onCitationClick }) => (
  <div className="diff-viewer">
    <h2>Change Summary</h2>
    <div className="summary">{summary}</div>
    
    <h3>Detailed Changes ({changes.length})</h3>
    <ul className="change-list">
      {changes.map((change, index) => {
        console.log('change:', change);
        const lineNumber = findCitation(change.search_string, diffText);
        
        return (
          <li key={index} className="detailed-change">
            <div className="change-header">
              <strong>{change.description}</strong>
              {lineNumber !== null && (
                <button 
                  className="citation-link"
                  onClick={() => onCitationClick?.(lineNumber)}
                  title={`Jump to line ${lineNumber}`}
                >
                  <span className="citation-icon">↗</span>
                  Line {lineNumber}
                </button>
              )}
            </div>
            <div 
              className="change-context"
              dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(change.context) }}
            />
          </li>
        );
      })}
    </ul>
  </div>
);

// Add demo mode functionality and UI elements
const DEMO_FILES = {
  source: {
    url: 'https://www.microsoft.com/licensing/docs/documents/download/OnlineSvcsConsolidatedSLA(WW)(English)(August2023)(CR).docx',
    name: 'MS SLA August 2023'
  },
  target: {
    url: 'https://www.microsoft.com/licensing/docs/documents/download/OnlineSvcsConsolidatedSLA(WW)(English)(November2023)(CR).docx',
    name: 'MS SLA November 2023'
  }
};

// Main App Component
function App() {
  const [sourceFile, setSourceFile] = useState<File | null>(null);
  const [targetFile, setTargetFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<DocumentComparisonResult | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>('summary');
  const [isDemoMode, setIsDemoMode] = useState(false);
  const [isDemoLoading, setIsDemoLoading] = useState(false);
  const [step, setStep] = useState<ComparisonStep>({ mode: null, stage: 'select' });
  const [activeLineNumber, setActiveLineNumber] = useState<number | undefined>();

  const loadDemoFiles = async () => {
    setStep({ mode: 'demo', stage: 'ready' });
    setError(null);
    
    const formData = new FormData();
    formData.append('source_url', DEMO_FILES.source.url);
    formData.append('target_url', DEMO_FILES.target.url);
    
    setSourceFile(new File([], DEMO_FILES.source.name));
    setTargetFile(new File([], DEMO_FILES.target.name));
  };

  const handleCompare = async () => {
    if (!sourceFile || !targetFile) return;
    setStep(prev => ({ ...prev, stage: 'comparing' }));
    setError(null);

    try {
      const formData = new FormData();
      if (step.mode === 'demo') {
        formData.append('source_url', DEMO_FILES.source.url);
        formData.append('target_url', DEMO_FILES.target.url);
      } else {
        formData.append('source', sourceFile);
        formData.append('target', targetFile);
      }

      const response = await fetch('/api/v1/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Failed to compare documents');

      const data: DocumentComparisonResult = await response.json();
      setResults(data);
      setStep(prev => ({ ...prev, stage: 'complete' }));

      if (data.warning) {
        setError('Warning: Documents appear to be significantly different');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Comparison failed');
      setResults(null);
      setStep(prev => ({ ...prev, stage: 'ready' }));
    }
  };

  const startNew = () => {
    setStep({ mode: null, stage: 'select' });
    setSourceFile(null);
    setTargetFile(null);
    setResults(null);
    setError(null);
    setActiveTab('summary');
  };

  const handleCitationClick = (lineNumber: number) => {
    setActiveTab('differences');
    setActiveLineNumber(lineNumber);
  };

  return (
    <div className="app-container">
      <Header />
      
      <main className="main-content">
        <div className="content-wrapper">
          {step.stage !== 'complete' ? (
            <>
              {step.mode === null ? (
                <div className="intro-section">
                  <h1>Compare Documents</h1>
                  <p>Choose your comparison method</p>
                  
                  <div className="mode-selection">
                    <Button onClick={() => setStep({ mode: 'upload', stage: 'ready' })}>
                      Upload Documents
                    </Button>
                    <Button onClick={loadDemoFiles}>
                      Try Demo (Microsoft SLA Comparison)
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="comparison-setup">
                  <div className="setup-header">
                    <h2>{step.mode === 'demo' ? 'Demo Comparison' : 'Document Upload'}</h2>
                    <button className="back-button" onClick={startNew}>
                      ← Choose Different Method
                    </button>
                  </div>

                  {step.mode === 'demo' ? (
                    <div className="demo-preview">
                      <p className="demo-description">
                        Compare changes between Microsoft's SLA documents from November and December 2023 (This is a demo, the produced results may not be accurate).
                      </p>
                      <div className="demo-files">
                        <div className="file-item">
                          <span className="file-label">Source:</span>
                          <span className="file-name">{DEMO_FILES.source.name}</span>
                        </div>
                        <div className="file-item">
                          <span className="file-label">Target:</span>
                          <span className="file-name">{DEMO_FILES.target.name}</span>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="file-upload-container">
                      <div className="file-upload-wrapper">
                        <label className="file-input-label" htmlFor="source-file">
                          Choose Source File
                        </label>
                        <input
                          id="source-file"
                          type="file"
                          accept=".docx"
                          onChange={(e) => setSourceFile(e.target.files?.[0] || null)}
                        />
                        <div className="file-name-display">
                          {sourceFile ? sourceFile.name : 'No file selected'}
                        </div>
                      </div>
                      <div className="file-upload-wrapper">
                        <label className="file-input-label" htmlFor="target-file">
                          Choose Target File
                        </label>
                        <input
                          id="target-file"
                          type="file"
                          accept=".docx"
                          onChange={(e) => setTargetFile(e.target.files?.[0] || null)}
                        />
                        <div className="file-name-display"></div>
                          {targetFile ? targetFile.name : 'No file selected'}
                        </div>
                      </div>
                  )}

                  <div className="action-buttons">
                    <Button
                      onClick={handleCompare}
                      disabled={!sourceFile || !targetFile || step.stage === 'comparing'}
                      loading={step.stage === 'comparing'}
                    >
                      {step.stage === 'comparing' ? 'Comparing...' : 'Compare Documents'}
                    </Button>
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="results-container">
              <div className="results-header">
                <TabSelector activeTab={activeTab} onTabChange={setActiveTab} />
                <Button onClick={startNew} className="new-comparison-button">
                  New Comparison
                </Button>
              </div>

              {error && <div className="error-message">{error}</div>}
              
              {activeTab === 'summary' && results && (
                <ChangelogViewer
                  summary={results.changelog.summary}
                  changes={results.changelog.changes}
                  diffText={results.diff_text}
                  onCitationClick={handleCitationClick}
                />
              )}
              
              {activeTab === 'differences' && results && (
                <DiffViewer
                  diffText={results.diff_text}
                  similarityScore={results.similarity_score}
                  warning={results.warning}
                  scrollToLine={activeLineNumber}
                />
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;