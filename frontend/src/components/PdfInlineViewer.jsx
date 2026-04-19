import { useEffect, useRef, useState } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { Loader2, AlertCircle, ChevronLeft, ChevronRight, ZoomIn, ZoomOut } from 'lucide-react';
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

// Use worker served from /public (static), avoids CRA/Webpack .mjs resolution errors.
pdfjs.GlobalWorkerOptions.workerSrc = `${process.env.PUBLIC_URL || ''}/pdf.worker.min.mjs`;

/**
 * Inline PDF viewer for the BookStudio RENDER step.
 * Renders via pdfjs-dist so it works consistently across browsers (and Playwright).
 */
export default function PdfInlineViewer({ fileUrl, onError }) {
  const [numPages, setNumPages] = useState(0);
  const [pageNumber, setPageNumber] = useState(1);
  const [scale, setScale] = useState(1.0);
  const [containerWidth, setContainerWidth] = useState(0);
  const [loadError, setLoadError] = useState(null);
  const containerRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const ro = new ResizeObserver((entries) => {
      const w = entries[0]?.contentRect?.width;
      if (w) setContainerWidth(w);
    });
    ro.observe(containerRef.current);
    return () => ro.disconnect();
  }, []);

  // Reset when file changes
  useEffect(() => {
    setPageNumber(1);
    setLoadError(null);
  }, [fileUrl]);

  const onDocLoad = ({ numPages: n }) => setNumPages(n);
  const onDocErr = (err) => {
    setLoadError(err?.message || String(err));
    onError?.(err);
  };

  return (
    <div ref={containerRef} className="w-full h-full flex flex-col bg-neutral-100" data-testid="pdf-inline-viewer">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-3 py-2 bg-white border-b text-xs gap-2">
        <div className="flex items-center gap-1">
          <button
            onClick={() => setPageNumber((p) => Math.max(1, p - 1))}
            disabled={pageNumber <= 1}
            data-testid="pdf-prev"
            className="p-1.5 rounded hover:bg-amber-50 disabled:opacity-30"
            title="Página anterior"
          >
            <ChevronLeft size={14} />
          </button>
          <span className="font-mono min-w-[70px] text-center" data-testid="pdf-page-indicator">
            {pageNumber} / {numPages || '—'}
          </span>
          <button
            onClick={() => setPageNumber((p) => Math.min(numPages || p, p + 1))}
            disabled={pageNumber >= numPages}
            data-testid="pdf-next"
            className="p-1.5 rounded hover:bg-amber-50 disabled:opacity-30"
            title="Próxima página"
          >
            <ChevronRight size={14} />
          </button>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setScale((s) => Math.max(0.4, s - 0.2))}
            className="p-1.5 rounded hover:bg-amber-50"
            data-testid="pdf-zoom-out"
            title="Reduzir zoom"
          >
            <ZoomOut size={14} />
          </button>
          <span className="font-mono min-w-[50px] text-center">{Math.round(scale * 100)}%</span>
          <button
            onClick={() => setScale((s) => Math.min(2.4, s + 0.2))}
            className="p-1.5 rounded hover:bg-amber-50"
            data-testid="pdf-zoom-in"
            title="Aumentar zoom"
          >
            <ZoomIn size={14} />
          </button>
        </div>
      </div>

      {/* Document */}
      <div className="flex-1 overflow-auto flex flex-col items-center py-4 px-2 bg-neutral-200">
        {loadError ? (
          <div className="text-red-600 flex flex-col items-center gap-2 mt-12" data-testid="pdf-error">
            <AlertCircle size={28} />
            <p className="text-sm font-medium">Erro ao carregar PDF</p>
            <p className="text-xs text-gray-500">{loadError}</p>
          </div>
        ) : (
          <Document
            file={fileUrl}
            onLoadSuccess={onDocLoad}
            onLoadError={onDocErr}
            loading={
              <div className="flex flex-col items-center gap-2 mt-12 text-gray-500">
                <Loader2 className="animate-spin text-amber-600" size={28} />
                <p className="text-xs">Processando PDF...</p>
              </div>
            }
          >
            <Page
              pageNumber={pageNumber}
              scale={scale}
              width={containerWidth ? Math.min(containerWidth - 40, 900) * scale : undefined}
              renderTextLayer={false}
              renderAnnotationLayer={false}
              className="shadow-xl"
            />
          </Document>
        )}
      </div>
    </div>
  );
}
