package main

import (
	"archive/tar"
	"bytes"
	"compress/gzip"
	"io"
	"log"
	"strings"
)

const MetaDataFilePrefix1 = "./._"
const MetaDataFilePrefix2 = "._"
const RootDirectoryPrefix = "./"
const SubDirectoryDelimiter = "/"
const TfFileSuffix = ".tf"

// UnzipArchive - Unzips a .tar.gz archive to a map where key is the file name and value is the file content
func UnzipArchive(zipFile []byte) (map[string]string, error) {
	bytesReader := bytes.NewReader(zipFile)

	gzipReader, err := getGzipReader(bytesReader)
	if err != nil {
		return map[string]string{}, err
	}

	return getFileMapFromGzip(gzipReader)
}

func getGzipReader(bytesReader io.Reader) (io.Reader, error) {
	gzipReader, err := gzip.NewReader(bytesReader)
	if err != nil {
		return bytes.NewReader([]byte{}), err
	}
	defer gzipReader.Close()

	return gzipReader, nil
}

func getFileMapFromGzip(gzipReader io.Reader) (map[string]string, error) {
	fileMap := make(map[string]string)
	tarReader := tar.NewReader(gzipReader)

	for {
		hdr, err := tarReader.Next()
		if err == io.EOF {
			break
		} else if err != nil {
			return fileMap, err
		}

		if hdr.Typeflag != tar.TypeReg {
			log.Printf("Skipping item %s of type %s", hdr.Name, string(hdr.Typeflag))
			continue
		}

		// File extension names within the zipped file will have to end with .tf
		// Hence header name will need to be at least 4 chars
		if len(hdr.Name) < 4 {
			log.Printf("Skipping non tf file %s",  hdr.Name)
			continue
		}

		if !strings.HasSuffix(hdr.Name, TfFileSuffix) {
			log.Printf("Skipping non tf file %s", hdr.Name)
			continue
		}

		if strings.HasPrefix(hdr.Name, MetaDataFilePrefix1) || strings.HasPrefix(hdr.Name, MetaDataFilePrefix2) {
			log.Printf("Skipping potential metadata file %s", hdr.Name)
			continue
		}

		if !strings.HasPrefix(hdr.Name, RootDirectoryPrefix) && strings.Contains(hdr.Name, SubDirectoryDelimiter) {
			log.Printf("Skipping file in subdirectory %s", hdr.Name)
			continue
		}

		if strings.HasPrefix(hdr.Name, RootDirectoryPrefix) && strings.Count(hdr.Name, SubDirectoryDelimiter) > 1 {
			log.Printf("Skipping file in subdirectory %s", hdr.Name)
			continue
		}

		log.Printf("Found HCL file %s", hdr.Name)

		data, err := io.ReadAll(tarReader)
		if err != nil {
			return fileMap, err
		}

		fileMap[hdr.Name] = string(data)
	}

	return fileMap, nil
}
