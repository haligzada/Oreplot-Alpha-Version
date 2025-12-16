import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import io
from datetime import datetime
import json


class DrillQAQCAnalyzer:
    
    REQUIRED_COLLAR_FIELDS = ['hole_id', 'x', 'y', 'z']
    REQUIRED_SURVEY_FIELDS = ['hole_id', 'depth', 'azimuth', 'dip']
    REQUIRED_ASSAY_FIELDS = ['hole_id', 'from_depth', 'to_depth']
    
    QC_SAMPLE_TYPES = ['standard', 'blank', 'duplicate', 'field_duplicate', 'check_lab']
    
    @staticmethod
    def parse_drill_database(file_bytes: bytes, file_name: str) -> Dict[str, Any]:
        """
        Parse drill database from CSV or XLSX file.
        Returns dict with dataframes for collar, survey, assay, and lithology tables.
        """
        try:
            file_ext = file_name.lower().split('.')[-1]
            
            if file_ext == 'csv':
                df = pd.read_csv(io.BytesIO(file_bytes))
                return {'main': df, 'file_type': 'csv'}
            
            elif file_ext in ['xlsx', 'xls']:
                excel_file = pd.ExcelFile(io.BytesIO(file_bytes))
                sheets = {}
                
                for sheet_name in excel_file.sheet_names:
                    sheets[sheet_name.lower()] = pd.read_excel(excel_file, sheet_name=sheet_name)
                
                return {'sheets': sheets, 'file_type': 'excel'}
            
            else:
                return {'error': f'Unsupported file type: {file_ext}'}
        
        except Exception as e:
            return {'error': f'Error parsing drill database: {str(e)}'}
    
    @staticmethod
    def validate_collar_data(df: pd.DataFrame) -> Dict[str, Any]:
        """Validate collar survey data"""
        issues = []
        stats = {}
        
        df.columns = [col.lower().strip() for col in df.columns]
        
        for field in DrillQAQCAnalyzer.REQUIRED_COLLAR_FIELDS:
            if field not in df.columns:
                issues.append(f"Missing required field: {field}")
        
        if not issues:
            missing_coords = df[['x', 'y', 'z']].isnull().any(axis=1).sum()
            if missing_coords > 0:
                issues.append(f"{missing_coords} holes with missing coordinates")
            
            duplicate_holes = df['hole_id'].duplicated().sum()
            if duplicate_holes > 0:
                issues.append(f"{duplicate_holes} duplicate hole IDs found")
            
            stats['total_holes'] = len(df)
            stats['unique_holes'] = df['hole_id'].nunique()
            stats['missing_coords'] = missing_coords
            stats['duplicate_holes'] = duplicate_holes
            
            if 'x' in df.columns and 'y' in df.columns:
                stats['spatial_extent'] = {
                    'x_min': float(df['x'].min()),
                    'x_max': float(df['x'].max()),
                    'y_min': float(df['y'].min()),
                    'y_max': float(df['y'].max()),
                    'z_min': float(df['z'].min()) if 'z' in df.columns else None,
                    'z_max': float(df['z'].max()) if 'z' in df.columns else None
                }
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'stats': stats
        }
    
    @staticmethod
    def validate_assay_intervals(df: pd.DataFrame) -> Dict[str, Any]:
        """Validate assay interval data for gaps, overlaps, and missing values"""
        issues = []
        stats = {}
        
        df.columns = [col.lower().strip() for col in df.columns]
        
        for field in DrillQAQCAnalyzer.REQUIRED_ASSAY_FIELDS:
            if field not in df.columns:
                issues.append(f"Missing required field: {field}")
                return {'valid': False, 'issues': issues, 'stats': {}}
        
        df = df.sort_values(['hole_id', 'from_depth'])
        
        gaps_found = 0
        overlaps_found = 0
        negative_intervals = 0
        
        for hole_id, group in df.groupby('hole_id'):
            group = group.sort_values('from_depth')
            
            for i in range(len(group) - 1):
                current_to = group.iloc[i]['to_depth']
                next_from = group.iloc[i + 1]['from_depth']
                
                if pd.notna(current_to) and pd.notna(next_from):
                    gap = next_from - current_to
                    if gap > 0.1:
                        gaps_found += 1
                    elif gap < -0.1:
                        overlaps_found += 1
            
            interval_lengths = group['to_depth'] - group['from_depth']
            negative_intervals += (interval_lengths < 0).sum()
        
        if gaps_found > 0:
            issues.append(f"{gaps_found} gaps found in sample intervals")
        if overlaps_found > 0:
            issues.append(f"{overlaps_found} overlaps found in sample intervals")
        if negative_intervals > 0:
            issues.append(f"{negative_intervals} negative interval lengths (from > to)")
        
        missing_values = df[['from_depth', 'to_depth']].isnull().sum()
        if missing_values.any():
            issues.append(f"Missing depth values: FROM={missing_values['from_depth']}, TO={missing_values['to_depth']}")
        
        stats['total_samples'] = len(df)
        stats['total_holes'] = df['hole_id'].nunique()
        stats['gaps'] = gaps_found
        stats['overlaps'] = overlaps_found
        stats['negative_intervals'] = negative_intervals
        stats['avg_sample_length'] = float((df['to_depth'] - df['from_depth']).mean())
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'stats': stats
        }
    
    @staticmethod
    def analyze_grade_distribution(df: pd.DataFrame, element_columns: List[str]) -> Dict[str, Any]:
        """Analyze grade distributions and identify outliers"""
        results = {}
        
        for element in element_columns:
            if element not in df.columns:
                continue
            
            values = pd.to_numeric(df[element], errors='coerce').dropna()
            
            if len(values) == 0:
                continue
            
            q1 = values.quantile(0.25)
            q3 = values.quantile(0.75)
            iqr = q3 - q1
            lower_fence = q1 - 1.5 * iqr
            upper_fence = q3 + 1.5 * iqr
            
            outliers = values[(values < lower_fence) | (values > upper_fence)]
            
            results[element] = {
                'count': len(values),
                'mean': float(values.mean()),
                'median': float(values.median()),
                'std': float(values.std()),
                'min': float(values.min()),
                'max': float(values.max()),
                'q1': float(q1),
                'q3': float(q3),
                'outlier_count': len(outliers),
                'outlier_percent': round(len(outliers) / len(values) * 100, 2),
                'upper_fence': float(upper_fence),
                'lower_fence': float(lower_fence)
            }
        
        return results
    
    @staticmethod
    def analyze_qc_samples(df: pd.DataFrame, sample_type_column: str = 'sample_type') -> Dict[str, Any]:
        """Analyze QC sample performance (standards, blanks, duplicates)"""
        results = {
            'qc_summary': {},
            'issues': []
        }
        
        if sample_type_column not in df.columns:
            results['issues'].append(f"Sample type column '{sample_type_column}' not found")
            return results
        
        df['sample_type_clean'] = df[sample_type_column].str.lower().str.strip()
        
        total_samples = len(df)
        qc_samples = df[df['sample_type_clean'].isin(DrillQAQCAnalyzer.QC_SAMPLE_TYPES)]
        qc_count = len(qc_samples)
        qc_percentage = round(qc_count / total_samples * 100, 2) if total_samples > 0 else 0
        
        results['qc_summary']['total_samples'] = total_samples
        results['qc_summary']['qc_samples'] = qc_count
        results['qc_summary']['qc_percentage'] = qc_percentage
        
        if qc_percentage < 5:
            results['issues'].append(f"QC samples only {qc_percentage}% of total (recommended minimum: 5-10%)")
        
        by_type = qc_samples['sample_type_clean'].value_counts().to_dict()
        results['qc_summary']['by_type'] = by_type
        
        standards = qc_samples[qc_samples['sample_type_clean'] == 'standard']
        blanks = qc_samples[qc_samples['sample_type_clean'] == 'blank']
        duplicates = qc_samples[qc_samples['sample_type_clean'].str.contains('duplicate', na=False)]
        
        results['qc_summary']['standards_count'] = len(standards)
        results['qc_summary']['blanks_count'] = len(blanks)
        results['qc_summary']['duplicates_count'] = len(duplicates)
        
        if len(standards) == 0:
            results['issues'].append("No standard samples found (required for accuracy monitoring)")
        if len(blanks) == 0:
            results['issues'].append("No blank samples found (required for contamination detection)")
        if len(duplicates) == 0:
            results['issues'].append("No duplicate samples found (required for precision monitoring)")
        
        return results
    
    @staticmethod
    def generate_qaqc_report(validation_results: Dict[str, Any]) -> str:
        """Generate a comprehensive QAQC report in text format"""
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("DRILL DATABASE QAQC REPORT")
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("=" * 80)
        report_lines.append("")
        
        if 'collar_validation' in validation_results:
            report_lines.append("COLLAR DATA VALIDATION")
            report_lines.append("-" * 80)
            collar = validation_results['collar_validation']
            report_lines.append(f"Status: {'PASS' if collar['valid'] else 'FAIL'}")
            
            if collar.get('stats'):
                stats = collar['stats']
                report_lines.append(f"Total Holes: {stats.get('total_holes', 'N/A')}")
                report_lines.append(f"Unique Holes: {stats.get('unique_holes', 'N/A')}")
                report_lines.append(f"Missing Coordinates: {stats.get('missing_coords', 'N/A')}")
                report_lines.append(f"Duplicate Hole IDs: {stats.get('duplicate_holes', 'N/A')}")
            
            if collar.get('issues'):
                report_lines.append("\nIssues Found:")
                for issue in collar['issues']:
                    report_lines.append(f"  - {issue}")
            report_lines.append("")
        
        if 'interval_validation' in validation_results:
            report_lines.append("ASSAY INTERVAL VALIDATION")
            report_lines.append("-" * 80)
            intervals = validation_results['interval_validation']
            report_lines.append(f"Status: {'PASS' if intervals['valid'] else 'FAIL'}")
            
            if intervals.get('stats'):
                stats = intervals['stats']
                report_lines.append(f"Total Samples: {stats.get('total_samples', 'N/A')}")
                report_lines.append(f"Total Holes: {stats.get('total_holes', 'N/A')}")
                report_lines.append(f"Gaps: {stats.get('gaps', 'N/A')}")
                report_lines.append(f"Overlaps: {stats.get('overlaps', 'N/A')}")
                report_lines.append(f"Negative Intervals: {stats.get('negative_intervals', 'N/A')}")
                report_lines.append(f"Avg Sample Length: {stats.get('avg_sample_length', 0):.2f}m")
            
            if intervals.get('issues'):
                report_lines.append("\nIssues Found:")
                for issue in intervals['issues']:
                    report_lines.append(f"  - {issue}")
            report_lines.append("")
        
        if 'grade_analysis' in validation_results:
            report_lines.append("GRADE DISTRIBUTION ANALYSIS")
            report_lines.append("-" * 80)
            for element, stats in validation_results['grade_analysis'].items():
                report_lines.append(f"\n{element.upper()}:")
                report_lines.append(f"  Count: {stats['count']}")
                report_lines.append(f"  Mean: {stats['mean']:.4f}")
                report_lines.append(f"  Median: {stats['median']:.4f}")
                report_lines.append(f"  Std Dev: {stats['std']:.4f}")
                report_lines.append(f"  Min: {stats['min']:.4f} | Max: {stats['max']:.4f}")
                report_lines.append(f"  Q1: {stats['q1']:.4f} | Q3: {stats['q3']:.4f}")
                report_lines.append(f"  Outliers: {stats['outlier_count']} ({stats['outlier_percent']}%)")
            report_lines.append("")
        
        if 'qc_analysis' in validation_results:
            report_lines.append("QC SAMPLE ANALYSIS")
            report_lines.append("-" * 80)
            qc = validation_results['qc_analysis']
            
            if qc.get('qc_summary'):
                summary = qc['qc_summary']
                report_lines.append(f"Total Samples: {summary.get('total_samples', 'N/A')}")
                report_lines.append(f"QC Samples: {summary.get('qc_samples', 'N/A')} ({summary.get('qc_percentage', 0)}%)")
                report_lines.append(f"  - Standards: {summary.get('standards_count', 0)}")
                report_lines.append(f"  - Blanks: {summary.get('blanks_count', 0)}")
                report_lines.append(f"  - Duplicates: {summary.get('duplicates_count', 0)}")
            
            if qc.get('issues'):
                report_lines.append("\nIssues Found:")
                for issue in qc['issues']:
                    report_lines.append(f"  - {issue}")
            report_lines.append("")
        
        report_lines.append("=" * 80)
        report_lines.append("END OF QAQC REPORT")
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)
    
    @staticmethod
    def calculate_qaqc_score(validation_results: Dict[str, Any]) -> Tuple[int, str]:
        """
        Calculate a QAQC score (0-10) based on validation results.
        Returns (score, rationale)
        """
        score = 10
        deductions = []
        
        if 'collar_validation' in validation_results:
            collar = validation_results['collar_validation']
            if not collar['valid']:
                score -= 2
                deductions.append("Collar data has critical issues")
            
            stats = collar.get('stats', {})
            if stats.get('duplicate_holes', 0) > 0:
                score -= 1
                deductions.append("Duplicate hole IDs found")
            if stats.get('missing_coords', 0) > 0:
                score -= 1
                deductions.append("Missing coordinate data")
        
        if 'interval_validation' in validation_results:
            intervals = validation_results['interval_validation']
            if not intervals['valid']:
                score -= 2
                deductions.append("Sample intervals have gaps/overlaps")
            
            stats = intervals.get('stats', {})
            if stats.get('negative_intervals', 0) > 0:
                score -= 1
                deductions.append("Negative sample intervals detected")
        
        if 'qc_analysis' in validation_results:
            qc = validation_results['qc_analysis']
            qc_pct = qc.get('qc_summary', {}).get('qc_percentage', 0)
            
            if qc_pct < 5:
                score -= 2
                deductions.append(f"Insufficient QC samples ({qc_pct}%, recommended: 5-10%)")
            
            summary = qc.get('qc_summary', {})
            if summary.get('standards_count', 0) == 0:
                score -= 1
                deductions.append("No standard samples for accuracy monitoring")
            if summary.get('blanks_count', 0) == 0:
                score -= 1
                deductions.append("No blank samples for contamination detection")
        
        if 'grade_analysis' in validation_results:
            grade = validation_results['grade_analysis']
            high_outlier_elements = [
                elem for elem, stats in grade.items()
                if stats.get('outlier_percent', 0) > 10
            ]
            if high_outlier_elements:
                score -= 1
                deductions.append(f"High outlier percentage in: {', '.join(high_outlier_elements)}")
        
        score = max(0, score)
        
        if score >= 9:
            rationale = "Excellent QAQC - data quality is high with minimal issues. "
        elif score >= 7:
            rationale = "Good QAQC - minor issues present but data is generally reliable. "
        elif score >= 5:
            rationale = "Moderate QAQC - several issues identified requiring attention. "
        else:
            rationale = "Poor QAQC - significant data quality issues present. "
        
        if deductions:
            rationale += "Issues: " + "; ".join(deductions)
        
        return score, rationale
    
    @staticmethod
    def perform_full_analysis(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive QAQC analysis on drill database.
        Returns validation results, scores, and report.
        """
        results = {}
        
        if 'error' in parsed_data:
            return {'error': parsed_data['error']}
        
        if parsed_data.get('file_type') == 'csv':
            df = parsed_data['main']
            
            if all(field in df.columns for field in ['hole_id', 'x', 'y']):
                results['collar_validation'] = DrillQAQCAnalyzer.validate_collar_data(df)
            
            if all(field in df.columns for field in ['hole_id', 'from_depth', 'to_depth']):
                results['interval_validation'] = DrillQAQCAnalyzer.validate_assay_intervals(df)
                
                element_cols = [col for col in df.columns if any(x in col.lower() for x in ['au', 'ag', 'cu', 'pb', 'zn', 'grade', 'ppm', 'pct'])]
                if element_cols:
                    results['grade_analysis'] = DrillQAQCAnalyzer.analyze_grade_distribution(df, element_cols)
                
                if 'sample_type' in df.columns:
                    results['qc_analysis'] = DrillQAQCAnalyzer.analyze_qc_samples(df)
        
        elif parsed_data.get('file_type') == 'excel':
            sheets = parsed_data['sheets']
            
            if 'collar' in sheets:
                results['collar_validation'] = DrillQAQCAnalyzer.validate_collar_data(sheets['collar'])
            
            assay_sheet = None
            for sheet_name in ['assay', 'assays', 'geochemistry', 'samples']:
                if sheet_name in sheets:
                    assay_sheet = sheets[sheet_name]
                    break
            
            if assay_sheet is not None:
                results['interval_validation'] = DrillQAQCAnalyzer.validate_assay_intervals(assay_sheet)
                
                element_cols = [col for col in assay_sheet.columns if any(x in col.lower() for x in ['au', 'ag', 'cu', 'pb', 'zn', 'grade', 'ppm', 'pct'])]
                if element_cols:
                    results['grade_analysis'] = DrillQAQCAnalyzer.analyze_grade_distribution(assay_sheet, element_cols)
                
                if 'sample_type' in assay_sheet.columns:
                    results['qc_analysis'] = DrillQAQCAnalyzer.analyze_qc_samples(assay_sheet)
        
        if results:
            qaqc_score, qaqc_rationale = DrillQAQCAnalyzer.calculate_qaqc_score(results)
            results['qaqc_score'] = qaqc_score
            results['qaqc_rationale'] = qaqc_rationale
            results['qaqc_report'] = DrillQAQCAnalyzer.generate_qaqc_report(results)
        
        return results
