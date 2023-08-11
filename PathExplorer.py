# -*- coding: utf-8 -*-
"""
Created on Tue Aug  8 15:42:28 2023

@author: agarc

"""
import os
# =============================================================================
# PathExplorer
# =============================================================================
class PathExplorer:
    """
    This class handles path and file/extension list by exploring folders.
    It also handle path/directory definitions and weither files exists
    """

    def __init__(self):
        pass

# =============================================================================
# user functions
# =============================================================================
    def get_all_files_paths(self, directory: str) -> list:
        """
        Explore the main folder and list all files, including their paths.
        Args:
        directory (str): The path of the directory to explore.
        Returns:
        list: A list of file paths.
        """
        if self._assert_directory(directory) == False:
            return

        file_paths = []
        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                file_paths.append(file_path)
        return file_paths
    
    def get_all_paths_with_extension_name(self, directory: str) -> dict:
        """
        Get a hashmap with file extensions lists of file paths
            with that extension as values.
        Args:
        directory (str): The path of the directory to explore.
        Returns:
        dict: A list  [file paths, file extensions]
        """

        all_file_paths = self.get_all_files_paths(directory)

        temp_extensions = set()
        paths_with_extension = []
        for file_path in all_file_paths:
            file_extension = self._get_single_file_extension(file_path)
            file_name = self._get_single_file_name(file_path)
            paths_with_extension.append({"file_path": file_path,
                                         "file_extension": file_extension,
                                         "file_name": file_name,
                                         "file_full_name": file_name + file_extension})

            temp_extensions.add(file_extension)
        print(temp_extensions)
        return paths_with_extension

# =============================================================================
# assert and internal functions
# =============================================================================
    def _get_single_file_extension(self, single_file_path: str) -> str:
        """
        Get the file extension of a single file.
        Args:
        single_file_path (str): The path of the file.
        Returns:
        str: The file extension.
        """
        _, file_extension = os.path.splitext(single_file_path)
        return file_extension.lower()

    def _get_single_file_name(self, single_file_path: str) -> str:
        """
        Get the file name without extension of a single file.
        Args:
        single_file_path (str): The path of the file.
        Returns:
        str: The file name without extension.
        """
        file_name, _ = os.path.splitext(single_file_path)
        return os.path.basename(file_name)

    def _split_path(self, path: str):
        """
        Split a path into subpath.
        Usefull to construct new paths.

        Parameters
        ----------
        path : str
            path string.

        Returns
        -------
        folders : list
            list of subpath.

        """
        folders = []
        while True:
            path, folder = os.path.split(path)
            if folder:
                folders.append(folder)
            else:
                if path:
                    folders.append(path)
                break
        folders.reverse()
        return folders

    def _assert_directory(self, directory: str):
        """
        check if the direcotry given starts with ./ or ../
        use only relative path please:)
        """

        if directory[0] == '.' or directory[0:2] == '..':
            return True
        else:
            print("Directory must start with './' or '../' ")
            return False

    def _assert_file_exists(self, file_path: str):
        """
        check if a file exists
        """
        if os.path.exists(file_path):
            return True
        else:
            print('This file does not exists')
            return False

    def _check_path_type(self, path: str):
        """
        check if the path is a directory or a file.
        """
        # if the path points towards a file we check if it exits
        if os.path.isfile(path):
            if self._assert_file_exists(path):
                return "File"

        # if path is a directory we check if it has the correct format './' '../'
        elif os.path.isdir(path):
            if self._assert_directory(path):
                return "Directory"

        else:
            return "Invalid path"
        
        
    def _filter_extensions(self, file_paths, read_only_extensions=[], ignore_extensions=[]) -> list:
        """
        Filter file paths based on their extensions.
        Parameters
        ----------
        file_paths : list
            A list of file paths to be filtered.
        read_only_extensions : list, optional
            A list of file extensions to include in the filtered list. If provided,
                only files with these extensions will be included.
        ignore_extensions : list, optional
            A list of file extensions to exclude from the filtered list. If
                provided, files with these extensions will be excluded.
        Returns
        -------
        list
            A list of filtered file paths based on the provided extension criteria.
        """
        # If read_only_extensions is provided, filter file_paths to include only
        if read_only_extensions:
            filtered_file_paths = [file_path for file_path in file_paths if self._get_single_file_extension(
                file_path) in read_only_extensions]
            return filtered_file_paths

        # If ignore_extensions is provided, filter file_paths to exclude files with
        if ignore_extensions:
            filtered_file_paths = [file_path for file_path in file_paths if self._get_single_file_extension(
                file_path) not in ignore_extensions]
            return filtered_file_paths

        # If no exclusion criteria are provided, return the original file_paths list
        return file_paths



    
if __name__ == "__main__":
    explorer = PathExplorer()
    directory = r'../_data_raw/'
    files = explorer.get_all_paths_with_extension_name(directory)


