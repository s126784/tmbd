import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

const ClusterVisualization = ({ data, onClusteringComplete }) => {
  const svgRef = useRef();

  useEffect(() => {
    if (!data || !data.embedding) return;

    const width = 800;
    const height = 600;
    const margin = { top: 20, right: 20, bottom: 30, left: 40 };

    // Clear previous visualization
    d3.select(svgRef.current).selectAll("*").remove();

    // Create SVG
    const svg = d3.select(svgRef.current)
      .attr("width", width)
      .attr("height", height);

    // Create scales
    const xScale = d3.scaleLinear()
      .domain(d3.extent(data.embedding, d => d[0]))
      .range([margin.left, width - margin.right]);

    const yScale = d3.scaleLinear()
      .domain(d3.extent(data.embedding, d => d[1]))
      .range([height - margin.bottom, margin.top]);

    // Create color scale for clusters
    const colorScale = d3.scaleOrdinal(d3.schemeCategory10);

    // Add points
    svg.selectAll("circle")
      .data(data.embedding)
      .enter()
      .append("circle")
      .attr("cx", d => xScale(d[0]))
      .attr("cy", d => yScale(d[1]))
      .attr("r", 5)
      .attr("fill", (d, i) => colorScale(i % 10))
      .attr("opacity", 0.6)
      .on("mouseover", function(event, d) {
        d3.select(this)
          .attr("r", 8)
          .attr("opacity", 1);
      })
      .on("mouseout", function(event, d) {
        d3.select(this)
          .attr("r", 5)
          .attr("opacity", 0.6);
      });

    // Add axes
    const xAxis = d3.axisBottom(xScale);
    const yAxis = d3.axisLeft(yScale);

    svg.append("g")
      .attr("transform", `translate(0,${height - margin.bottom})`)
      .call(xAxis);

    svg.append("g")
      .attr("transform", `translate(${margin.left},0)`)
      .call(yAxis);

    // Simulate clustering completion
    const mockClusters = data.embedding.map((point, i) => ({
      id: i,
      cluster: Math.floor(Math.random() * 5)
    }));

    onClusteringComplete(mockClusters);
  }, [data, onClusteringComplete]);

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h2 className="text-xl font-semibold mb-4">Document Clusters</h2>
      <div className="overflow-x-auto">
        <svg ref={svgRef} className="mx-auto"></svg>
      </div>
    </div>
  );
};

export default ClusterVisualization;
