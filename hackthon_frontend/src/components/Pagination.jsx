import React from "react";

function Pagination({
  currentPage,
  totalPages,
  totalCount,
  pageSize,
  onPageChange,
  maxPageButtons = 5,
  size = "md",
}) {
  // If no pages, don't render pagination
  if (totalPages <= 1) return null;

  // Calculate the range of page numbers to display
  const getPageNumbers = () => {
    const pages = [];
    let startPage, endPage;

    if (totalPages <= maxPageButtons) {
      // Show all pages if total pages is less than max buttons
      startPage = 1;
      endPage = totalPages;
    } else {
      // Calculate start and end pages
      const halfButtons = Math.floor(maxPageButtons / 2);
      
      if (currentPage <= halfButtons) {
        startPage = 1;
        endPage = maxPageButtons;
      } else if (currentPage + halfButtons >= totalPages) {
        startPage = totalPages - maxPageButtons + 1;
        endPage = totalPages;
      } else {
        startPage = currentPage - halfButtons;
        endPage = currentPage + halfButtons;
      }
    }

    for (let i = startPage; i <= endPage; i++) {
      pages.push(i);
    }

    return pages;
  };

  const pageNumbers = getPageNumbers();
  const hasPrevious = currentPage > 1;
  const hasNext = currentPage < totalPages;

  // Calculate showing range
  const startItem = (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, totalCount);

  // Button size classes
  const sizeClasses = {
    sm: "btn-sm",
    md: "",
    lg: "btn-lg",
  };

  const buttonSize = sizeClasses[size] || "";

  return (
    <div className="flex flex-col gap-4 mt-4">
      {/* Showing info */}
      <div className="text-muted text-sm text-gray-600">
        Showing <strong>{startItem}</strong> to <strong>{endItem}</strong> of{" "}
        <strong>{totalCount}</strong> results
      </div>

      {/* Pagination buttons */}
      <nav aria-label="Page navigation" className="flex justify-center w-full">
        <ul className="pagination mb-0 flex flex-wrap justify-center">
          {/* First page button */}
          <li className={`page-item ${!hasPrevious ? "disabled" : ""}`}>
            <button
              className={`page-link ${buttonSize}`}
              onClick={() => onPageChange(1)}
              disabled={!hasPrevious}
              aria-label="First"
              style={{ borderRadius: "6px 0 0 6px" }}
            >
              <i className="bi bi-chevron-double-left"></i>
            </button>
          </li>

          {/* Previous button */}
          <li className={`page-item ${!hasPrevious ? "disabled" : ""}`}>
            <button
              className={`page-link ${buttonSize}`}
              onClick={() => onPageChange(currentPage - 1)}
              disabled={!hasPrevious}
              aria-label="Previous"
            >
              <i className="bi bi-chevron-left"></i>
            </button>
          </li>

          {/* Show ellipsis if needed at start */}
          {pageNumbers[0] > 1 && (
            <li className="page-item disabled">
              <span className={`page-link ${buttonSize}`}>...</span>
            </li>
          )}

          {/* Page number buttons */}
          {pageNumbers.map((pageNum) => (
            <li
              key={pageNum}
              className={`page-item ${pageNum === currentPage ? "active" : ""}`}
            >
              <button
                className={`page-link ${buttonSize}`}
                onClick={() => onPageChange(pageNum)}
                style={
                  pageNum === currentPage
                    ? {
                        background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                        border: "none",
                      }
                    : {}
                }
              >
                {pageNum}
              </button>
            </li>
          ))}

          {/* Show ellipsis if needed at end */}
          {pageNumbers[pageNumbers.length - 1] < totalPages && (
            <li className="page-item disabled">
              <span className={`page-link ${buttonSize}`}>...</span>
            </li>
          )}

          {/* Next button */}
          <li className={`page-item ${!hasNext ? "disabled" : ""}`}>
            <button
              className={`page-link ${buttonSize}`}
              onClick={() => onPageChange(currentPage + 1)}
              disabled={!hasNext}
              aria-label="Next"
            >
              <i className="bi bi-chevron-right"></i>
            </button>
          </li>

          {/* Last page button */}
          <li className={`page-item ${!hasNext ? "disabled" : ""}`}>
            <button
              className={`page-link ${buttonSize}`}
              onClick={() => onPageChange(totalPages)}
              disabled={!hasNext}
              aria-label="Last"
              style={{ borderRadius: "0 6px 6px 0" }}
            >
              <i className="bi bi-chevron-double-right"></i>
            </button>
          </li>
        </ul>
      </nav>
    </div>
  );
}

export default Pagination;